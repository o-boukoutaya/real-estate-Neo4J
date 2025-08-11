# Ce fichier doit contenir la logique de fusion Retriever (KG + Vector)

# backend/rag/retriever.py
from __future__ import annotations
from typing import List, Dict
from neo4j import Driver
from embedding.embedding_manager import EmbeddingManager
from embedding.vector_store import Neo4jVectorManager
from utils.logging import get_logger

logger = get_logger(__name__)


class Retriever:
    """
    Hybride — similarity search (vector index) + expansion KG (Cypher).
    """

    def __init__(
        self,
        embedder: EmbeddingManager,
        vector_store: Neo4jVectorManager,
        kg_driver: Driver,
    ):
        self.embedder = embedder
        self.vstore = vector_store
        self.driver = kg_driver

    # ---------- Vector --------------------------------------------------
    def _vector_hits(self, question: str, k: int = 8) -> List[Dict]:
        try:
            vec = self.embedder.embed_texts([question])[0]
            return self.vstore.search_similar(vec, k=k)
        except Exception as e:
            logger.error('Vector search failed: %s', e)
            return []

    # ---------- Entities ------------------------------------------------
    @staticmethod
    def _extract_entities(texts: List[str]) -> List[str]:
        """Ultra-léger : tous les mots Capitalisés (à remplacer par vrai NER)."""
        import re

        entities = set()
        for t in texts:
            entities |= set(re.findall(r"\b[A-ZÉÈÂÀÄ][\w’\-]{2,}", t))
        return list(entities)

    # ---------- Cypher --------------------------------------------------
    def _kg_hits(self, entities: List[str], hops: int = 1) -> List[Dict]:
        cypher = f"""
        UNWIND $ents AS e
        MATCH (n:Entity {{name:e}})-[*1..{hops}]-(m:Entity)
        WITH DISTINCT m LIMIT 30
        RETURN m.name   AS name,
               labels(m) AS labels
        """
        try:
            with self.driver.session() as s:
                return [dict(r) for r in s.run(cypher, ents=entities)]
        except Exception as e:
            logger.error('KG search failed: %s', e)
            return []

    # ---------- Public API ---------------------------------------------
    def retrieve(self, question: str, *, k: int = 8) -> Dict:
        try:
            v_hits = self._vector_hits(question, k=k)
            ents = self._extract_entities([h['text'] for h in v_hits])
            kg_hits = self._kg_hits(ents)
            return {"vector_hits": v_hits, "cypher_hits": kg_hits}
        except Exception as e:
            logger.error('Retrieve failed: %s', e)
            return {"vector_hits": [], "cypher_hits": []}
