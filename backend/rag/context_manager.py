# backend/rag/context_manager.py
from typing import Dict, List


class ContextManager:
    @staticmethod
    def merge(vector_hits: List[Dict], cypher_hits: List[Dict], limit: int = 20) -> str:
        passages = [h["text"] for h in vector_hits][:limit]
        entities = [f"{h['name']} ({', '.join(h['labels'])})" for h in cypher_hits][:limit]
        return "\n".join(passages + entities)
