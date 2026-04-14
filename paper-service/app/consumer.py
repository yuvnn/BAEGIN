import os
import json
import logging
import threading
import time
from kafka import KafkaConsumer
from sqlalchemy.orm import Session

from .evaluator import evaluate_paper
from .summarizer import summarize_paper
from .chroma_client import store_paper, query_internal_docs
from .pdf_parser import download_and_parse_pdf
from .database import SessionLocal
from .models import PaperSummary, PaperRelate

logger = logging.getLogger(__name__)

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_PAPERS", "new_papers_topic")

# arXiv 태그 → 대분류 매핑
_ARXIV_TO_CATEGORY = {
    "cs.CL": "Language & Text",
    "cs.CV": "Vision & Graphics",
    "cs.GR": "Vision & Graphics",
    "cs.RO": "Robotics & Control",
    "cs.SY": "Robotics & Control",
    "eess.SY": "Robotics & Control",
    "cs.MA": "Multi-Agent & RL",
    "cs.GT": "Multi-Agent & RL",
    "cs.CY": "Ethics & Society",
    "cs.HC": "Ethics & Society",
    "cs.LG": "ML Foundation",
    "cs.AI": "ML Foundation",
    "cs.NE": "ML Foundation",
    "stat.ML": "ML Foundation",
}

# 특정 대분류가 여러 개 매핑될 때의 우선순위 (위에서 낮을수록 우선)
_CATEGORY_PRIORITY = [
    "Language & Text",
    "Vision & Graphics",
    "Robotics & Control",
    "Multi-Agent & RL",
    "Ethics & Society",
    "ML Foundation",
]

def classify_category(arxiv_categories: list) -> str:
    """arXiv 태그 목록을 받아 프로젝트 대분류를 반환합니다.

    여러 태그가 다른 대분류로 매핑될 경우 _CATEGORY_PRIORITY 순서대로 반환합니다.
    알 수 없는 태그만 있을 경우 'ML Foundation'을 기본값으로 반환합니다.
    """
    matched = {_ARXIV_TO_CATEGORY[c] for c in arxiv_categories if c in _ARXIV_TO_CATEGORY}
    if not matched:
        return "ML Foundation"
    for cat in _CATEGORY_PRIORITY:
        if cat in matched:
            return cat
    return "ML Foundation"

def consume_papers():
    consumer = None
    # Retry connection to Kafka
    for i in range(10):
        try:
            logger.info(f"Attempting to connect to Kafka at {KAFKA_BROKER} (Attempt {i+1}/10)...")
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=[KAFKA_BROKER],
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id='paper-service-group',
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
                max_poll_interval_ms=1800000,  # 30 min: AI evaluation per paper ~30-40s
                request_timeout_ms=40000,
                connections_max_idle_ms=60000
            )
            logger.info(f"✅ Successfully connected to Kafka broker. Listening to topic '{KAFKA_TOPIC}'")
            break
        except Exception as e:
            logger.error(f"❌ Failed to connect to Kafka: {e}")
            time.sleep(5)
    
    if not consumer:
        logger.critical("Could not establish Kafka connection. Background consumer thread exiting.")
        return

    logger.info("Kafka consumer loop started. Waiting for messages...")
    for message in consumer:
        db: Session = SessionLocal()
        try:
            paper_data = message.value
            logger.info(f"📥 Received Kafka message: {paper_data.get('paper_id')}")
            
            doc_id = paper_data.get("paper_id")
            keyword = paper_data.get("keyword", "AI")
            title = paper_data.get("title", "")
            abstract = paper_data.get("abstract", "")
            pdf_url = paper_data.get("pdf_url", "")
            paper_url = paper_data.get("url", "")
            authors = paper_data.get("authors", [])
            arxiv_categories = paper_data.get("arxiv_categories", [])
            category = classify_category(arxiv_categories)
            
            if not all([doc_id, title, abstract]):
                logger.warning(f"⚠️ Incomplete paper data received: {paper_data}")
                continue

            logger.info(f"🔍 Processing paper: {title}")
            
            # Step 1: Download and Parse PDF first
            full_text = ""
            if pdf_url:
                logger.info(f"📥 Downloading PDF from {pdf_url} for evaluation...")
                full_text = download_and_parse_pdf(pdf_url)
            else:
                logger.warning(f"⚠️ No pdf_url provided for {doc_id}. Proceeding with abstract only.")

            # Step 2: Evaluate using AI Scientist pipeline
            logger.info(f"🧠 Evaluating paper '{title}' with AI Scientist pipeline...")
            evaluation = evaluate_paper(keyword, title, abstract, full_text=full_text)
            
            if evaluation.is_relevant:
                logger.info(f"✅ Paper '{title}' PASSED (Score: {evaluation.score}, Decision: {evaluation.decision}). Summarizing...")
                
                # Step 3: Summarize using full text
                summary_dict = summarize_paper(doc_id, title, abstract, body_text=full_text)
                md_summary = summary_dict.get("summary", "")
                
                # RDB Save
                db_summary = PaperSummary(
                    paper_id=doc_id,
                    md_summary=md_summary,
                    paper_url=paper_url,
                    authors=json.dumps(authors, ensure_ascii=False),
                    category=category
                )
                db.merge(db_summary)
                db.commit()
                logger.info(f"💾 Saved PaperSummary for '{doc_id}' to MariaDB.")

                # ChromaDB Save
                metadata = {
                    "source_type": "paper",
                    "document_type": "paper",
                    "access_level": "public",
                    "title": title,
                    "keyword": keyword,
                    "category": category,
                    "arxiv_categories": ",".join(arxiv_categories),
                    "evaluation_score": evaluation.score,
                    "evaluation_review": evaluation.review
                }
                store_paper(doc_id, json.dumps(summary_dict, ensure_ascii=False), metadata)
                
                # Similarity Mapping
                logger.info(f"🔎 Querying internal_docs for similarities...")
                internal_results = query_internal_docs(md_summary, n_results=50)
                
                # (Logic for rank/reason remains same as before...)
                internal_docs_found = {}
                paper_relates = {}
                current_rank = 1
                
                if internal_results and "ids" in internal_results and internal_results["ids"]:
                    ids = internal_results["ids"][0]
                    docs = internal_results["documents"][0]
                    metas = internal_results["metadatas"][0]
                    
                    for i in range(len(ids)):
                        if current_rank > 10: break
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
                            paper_relates[internal_doc_id]["reason"] += f"\n- **추가 유사 청크**: {chunk_text}\n"
                            
                for _, relate_data in paper_relates.items():
                    db_relate = PaperRelate(
                        paper_id=doc_id,
                        internal_doc_id=relate_data["internal_doc_id"],
                        rank=relate_data["rank"],
                        reason=relate_data["reason"]
                    )
                    db.merge(db_relate)
                
                if paper_relates:
                    db.commit()
                    logger.info(f"💾 Saved {len(paper_relates)} PaperRelate records for '{doc_id}' to MariaDB.")
            else:
                logger.info(f"❌ Paper '{title}' was REJECTED (Score: {evaluation.score}). Reason: {evaluation.review[:100]}...")
                
        except Exception as e:
            logger.error(f"💥 Error processing Kafka message: {e}")
            db.rollback()
        finally:
            db.close()

def start_kafka_consumer():
    """Starts the Kafka consumer in a background thread."""
    thread = threading.Thread(target=consume_papers, daemon=True)
    thread.start()
    logger.info("Kafka consumer thread dispatched.")
