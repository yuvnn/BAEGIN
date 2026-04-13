import os
import json
import logging
import threading
from kafka import KafkaConsumer
from .evaluator import evaluate_paper
from .summarizer import summarize_paper
from .chroma_client import store_paper
from .pdf_parser import download_and_parse_pdf

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
        try:
            paper_data = message.value
            doc_id = paper_data.get("paper_id")
            keyword = paper_data.get("keyword", "AI")
            title = paper_data.get("title", "")
            abstract = paper_data.get("abstract", "")
            pdf_url = paper_data.get("pdf_url", "")
            
            if not all([doc_id, title, abstract]):
                logger.warning(f"Incomplete paper data received: {paper_data}")
                continue

            logger.info(f"Evaluating paper: {title}")
            evaluation = evaluate_paper(keyword, title, abstract)
            
            if evaluation.is_relevant:
                logger.info(f"Paper '{title}' passed evaluation (Score: {evaluation.score}). Downloading PDF for full summarization...")
                
                full_text = ""
                if pdf_url:
                    full_text = download_and_parse_pdf(pdf_url)
                else:
                    logger.warning(f"No pdf_url provided for {doc_id}. Falling back to abstract-only summarization.")

                summary_dict = summarize_paper(doc_id, title, abstract, body_text=full_text)
                
                metadata = {
                    "source_type": "paper",
                    "document_type": "paper",
                    "access_level": "public",
                    "title": title,
                    "keyword": keyword,
                    "evaluation_score": evaluation.score,
                    "evaluation_review": evaluation.review
                }
                
                logger.info(f"Storing paper '{title}' into ChromaDB...")
                # We store the stringified JSON from summary_dict as the document text
                store_paper(doc_id, json.dumps(summary_dict, ensure_ascii=False), metadata)
            else:
                logger.info(f"Paper '{title}' was rejected (Score: {evaluation.score}). Reason: {evaluation.review}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")

def start_kafka_consumer():
    """Starts the Kafka consumer in a background thread."""
    thread = threading.Thread(target=consume_papers, daemon=True)
    thread.start()
    logger.info("Kafka consumer thread started.")
