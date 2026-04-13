import json
import logging
import os
from datetime import datetime

from kafka import KafkaProducer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)

TOPIC = "new_papers_topic"


class KafkaEventPublisher:
    def __init__(self) -> None:
        self._producer: KafkaProducer | None = None

    def connect(self) -> None:
        """Create the Kafka producer. Called once at app startup."""
        bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        try:
            self._producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                request_timeout_ms=5000,
                max_block_ms=5000,
            )
            logger.info("Kafka producer connected to %s", bootstrap_servers)
        except Exception as exc:
            logger.warning(
                "Kafka producer could not connect to %s: %s — running without Kafka",
                bootstrap_servers,
                exc,
            )
            self._producer = None

    def publish(self, paper: dict, keyword: str = "") -> bool:
        """Publish a new_paper_detected event.

        Returns True on success, False if Kafka is unavailable or publish fails.
        """
        if self._producer is None:
            logger.debug("Kafka unavailable; skipping publish for paper_id=%s", paper.get("paper_id"))
            return False

        event = {
            "event_type": "new_paper_detected",
            "paper_id": paper["paper_id"],
            "keyword": keyword,
            "title": paper["title"],
            "abstract": paper.get("abstract", ""),
            "authors": paper.get("authors", []),
            "source": paper.get("source", "unknown"),
            "url": paper.get("url", ""),
            "pdf_url": paper.get("pdf_url"),
            "published_at": paper.get("published_at", datetime.utcnow().isoformat()),
            "detected_at": datetime.utcnow().isoformat(),
        }
        try:
            future = self._producer.send(TOPIC, value=event)
            self._producer.flush(timeout=5)
            future.get(timeout=5)
            logger.info("Published event for paper_id=%s", paper["paper_id"])
            return True
        except KafkaError as exc:
            logger.warning("Kafka publish failed for paper_id=%s: %s", paper["paper_id"], exc)
            return False
        except Exception as exc:
            logger.warning("Unexpected error publishing to Kafka: %s", exc)
            return False

    def close(self) -> None:
        """Close the Kafka producer. Called once at app shutdown."""
        if self._producer is not None:
            try:
                self._producer.close(timeout=5)
            except Exception as exc:
                logger.warning("Error closing Kafka producer: %s", exc)
            finally:
                self._producer = None
            logger.info("Kafka producer closed.")


kafka_publisher = KafkaEventPublisher()
