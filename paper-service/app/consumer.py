import os
import json
import logging
import threading
from kafka import KafkaConsumer
from sqlalchemy.orm import Session

from .evaluator import evaluate_paper
from .summarizer import summarize_paper
from .chroma_client import store_paper, query_internal_docs
from .pdf_parser import download_and_parse_pdf
from .database import SessionLocal
from .models import PaperSummary, PaperRelate

logger = logging.getLogger(__name__)

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_PAPERS", "new_papers_topic")

def consume_papers():
    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=[KAFKA_BROKER],
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='paper-service-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        logger.info(f"Connected to Kafka broker at {KAFKA_BROKER}, listening to topic '{KAFKA_TOPIC}'")
    except Exception as e:
        logger.error(f"Failed to connect to Kafka: {e}")
        return

    for message in consumer:
        db: Session = SessionLocal()
        try:
            paper_data = message.value
            doc_id = paper_data.get("paper_id")
            keyword = paper_data.get("keyword", "AI")
            title = paper_data.get("title", "")
            abstract = paper_data.get("abstract", "")
            pdf_url = paper_data.get("pdf_url", "")
            paper_url = paper_data.get("url", "")
            authors = paper_data.get("authors", [])
            
            if not all([doc_id, title, abstract]):
                logger.warning(f"Incomplete paper data received: {paper_data}")
                continue

            logger.info(f"Processing paper: {title}")
            
            # Step 1: Download and Parse PDF first to get full text for rigorous evaluation
            full_text = ""
            if pdf_url:
                logger.info(f"Downloading PDF from {pdf_url} for evaluation...")
                full_text = download_and_parse_pdf(pdf_url)
            else:
                logger.warning(f"No pdf_url provided for {doc_id}. Proceeding with abstract only.")

            # Step 2: Evaluate using AI Scientist pipeline (Full text if available)
            logger.info(f"Evaluating paper with AI Scientist pipeline...")
            evaluation = evaluate_paper(keyword, title, abstract, full_text=full_text)
            
            if evaluation.is_relevant:
                logger.info(f"Paper '{title}' PASSED evaluation (Score: {evaluation.score}, Decision: {evaluation.decision}).")
                
                # Step 3: Summarize using the already extracted full text
                summary_dict = summarize_paper(doc_id, title, abstract, body_text=full_text)
                md_summary = summary_dict.get("summary", "")
                
                # 1. Save to RDB: PaperSummary
                db_summary = PaperSummary(
                    paper_id=doc_id,
                    md_summary=md_summary,
                    paper_url=paper_url,
                    authors=json.dumps(authors, ensure_ascii=False),
                    category=keyword
                )
                db.merge(db_summary)
                db.commit()
                logger.info(f"Saved PaperSummary for '{doc_id}' to MariaDB.")

                # 2. Store to ChromaDB (papers collection)
                metadata = {
                    "source_type": "paper",
                    "document_type": "paper",
                    "access_level": "public",
                    "title": title,
                    "keyword": keyword,
                    "evaluation_score": evaluation.score,
                    "evaluation_review": evaluation.review
                }
                store_paper(doc_id, json.dumps(summary_dict, ensure_ascii=False), metadata)
                
                # 3. Query internal_docs and process PaperRelate
                logger.info(f"Querying internal_docs for similarities...")
                internal_results = query_internal_docs(md_summary, n_results=50)
                
                internal_docs_found = {} # doc_id -> rank
                paper_relates = {} # doc_id -> dict of data
                current_rank = 1
                
                if internal_results and "ids" in internal_results and internal_results["ids"]:
                    # results structure is lists of lists
                    ids = internal_results["ids"][0]
                    docs = internal_results["documents"][0]
                    metas = internal_results["metadatas"][0]
                    
                    for i in range(len(ids)):
                        if current_rank > 10:
                            break
                            
                        meta = metas[i] if metas else {}
                        chunk_text = docs[i]
                        internal_doc_id = meta.get("doc_id", "unknown_doc")
                        source_file = meta.get("source_file", "Unknown File")
                        
                        if internal_doc_id not in internal_docs_found:
                            internal_docs_found[internal_doc_id] = current_rank
                            paper_relates[internal_doc_id] = {
                                "internal_doc_id": internal_doc_id,
                                "rank": current_rank,
                                "reason": f"### 매칭된 내부 문서: {source_file}\n\n- **유사 청크 1**: {chunk_text}\n"
                            }
                            current_rank += 1
                        else:
                            # Append chunk to reason
                            paper_relates[internal_doc_id]["reason"] += f"\n- **추가 유사 청크**: {chunk_text}\n"
                            
                # 4. Save to RDB: PaperRelate
                for doc_ref, relate_data in paper_relates.items():
                    db_relate = PaperRelate(
                        paper_id=doc_id,
                        internal_doc_id=relate_data["internal_doc_id"],
                        rank=relate_data["rank"],
                        reason=relate_data["reason"]
                    )
                    db.merge(db_relate)
                
                if paper_relates:
                    db.commit()
                    logger.info(f"Saved {len(paper_relates)} PaperRelate records for '{doc_id}' to MariaDB.")
                
            else:
                logger.info(f"Paper '{title}' was rejected (Score: {evaluation.score}). Reason: {evaluation.review}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            db.rollback()
        finally:
            db.close()

def start_kafka_consumer():
    """Starts the Kafka consumer in a background thread."""
    thread = threading.Thread(target=consume_papers, daemon=True)
    thread.start()
    logger.info("Kafka consumer thread started.")
