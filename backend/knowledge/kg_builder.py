"""Extraction rapide triplets (LLM) -> Neo4j."""
from neo4j import GraphDatabase
from embedding.vector_store import Neo4jVectorManager
from knowledge.graph_builder import GraphBuilder
from knowledge.schema_manager import GraphSchemaManager
from pathlib import Path
from typing import List, Dict
import os
from utils.logging import get_logger

logger = get_logger(__name__)


class KGBuilder:
    def __init__(self, *, driver, database: str, llm, schema_manager, extracted_dir=None):
        from pathlib import Path
        self.driver = driver
        self.db     = database                # <- mémoriser la base cible
        self.chain = llm
        self.schema_mgr = schema_manager
        self.extracted_dir = extracted_dir or os.path.join(os.path.dirname(__file__), '..', 'data', 'chunks')

    # ------------------------------------------------------------------
    def _load_series_texts(self, series_version: str) -> List[str]:
        """Retourne la liste des textes contenus dans *data/chunks/chunks_<series_version>/*.txt*"""
        try:
            d = os.path.normpath(os.path.join(self.extracted_dir, f"chunks_{series_version}"))
            d = Path(d)
            if not d.exists():
                raise FileNotFoundError(f"Répertoire introuvable : {d}")
            files = sorted(d.glob("*.txt"))
            if not files:
                raise RuntimeError("Aucun chunk trouvé dans le dossier : " + d.as_posix())
            return [p.read_text(encoding="utf-8") for p in files]
        except Exception as e:
            logger.error("Erreur lors du chargement de la série %s: %s", series_version, e)
            raise

    # ------------------------------------------------------------------
    def build_from_text(self, text: str) -> int:
        try:
            triplets = self.chain.extract_relations(text)
            cypher_tmpl = """
        UNWIND $rows AS r
        MERGE (s:Entity {name:r.s})
        MERGE (o:Entity {name:r.o})
        MERGE (s)-[:`%s`]->(o)
        """
            rows = [{"s": t.subject, "o": t.object, "rel": t.relation} for t in triplets]
            with self.driver.session() as s:
                for rel in {r["rel"] for r in rows}:
                    s.run(cypher_tmpl % rel.upper(),
                          rows=[r for r in rows if r["rel"] == rel])
            return len(triplets)
        except Exception as e:
            logger.error("Erreur lors de la construction du texte: %s", e)
            raise

    # ------------------------------------------------------------------
    def build_from_series(self, series_version: str) -> dict:
        """Construit le KG à partir des chunks au lieu du fichier texte d'origine."""
        try:
            texts = self._load_series_texts(series_version)
            return self.build_from_chunks(texts)
        except Exception as e:
            logger.error("Erreur lors de la construction de la série %s: %s", series_version, e)
            raise

    # ------------------------------------------------------------------
    def build_from_chunks(self, chunks: list[str]) -> dict:
        """Construit le KG à partir des chunks au lieu du fichier texte d'origine."""
        try:
            full_text = "\n".join(chunks)
            if not full_text.strip():
                raise ValueError("Input text for relation extraction is empty.")
            triplets = self.build_from_text(full_text)
            return {"triplets_created": triplets, "chunks_used": len(chunks)}
        except Exception as e:
            logger.error("Erreur lors de la construction à partir des chunks: %s", e)
            raise

    # ------------------------------------------------------------------
    def check_kg_exists(self) -> bool:
        """Retourne True si **au moins un nœud du KG** est présent dans la base configurée."""
        cypher = """
        MATCH (n)
        WHERE any(lbl IN labels(n)
                  WHERE lbl IN ['Chunk','Entity','Document'])
        RETURN COUNT(n) > 0 AS exists
        """
        try:
            with self.driver.session(database=self.db) as s:
                return s.run(cypher).single()["exists"]
        except Exception as e:
            logger.error("Erreur lors de la vérification du KG: %s", e)
            return False
