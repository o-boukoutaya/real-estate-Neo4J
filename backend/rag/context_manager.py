from typing import Dict, List
from utils.logging import get_logger

logger = get_logger(__name__)


class ContextManager:
    @staticmethod
    def merge(vector_hits: List[Dict], cypher_hits: List[Dict], limit: int = 20) -> str:
        try:
            passages = [h["text"] for h in vector_hits][:limit]
            entities = [f"{h['name']} ({', '.join(h['labels'])})" for h in cypher_hits][:limit]
            return "\n".join(passages + entities)
        except Exception as e:
            logger.error("Context merge failed: %s", e)
            return ""
