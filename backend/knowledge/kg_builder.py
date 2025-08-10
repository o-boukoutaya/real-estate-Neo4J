"""Extraction rapide triplets (LLM) -> Neo4j."""
from neo4j import GraphDatabase
from embedding.vector_store import Neo4jVectorManager
from knowledge.graph_builder import GraphBuilder
from knowledge.schema_manager import GraphSchemaManager
from pathlib import Path
from typing import List, Dict
import os

class KGBuilder:
    def __init__(self, *, driver, database: str, llm, schema_manager, extracted_dir=None):
        from pathlib import Path
        self.driver = driver
        self.db     = database                # <- mémoriser la base cible
        self.chain = llm
        self.schema_mgr = schema_manager
        # self.extracted_dir = Path(extracted_dir)      # <-- changement majeur
        self.extracted_dir = extracted_dir or os.path.join(os.path.dirname(__file__), '..', 'data', 'chunks')
        # self.chunks_root: Path = Path("data/chunks")
    
    # ------------------------------------------------------------------
    def _load_series_texts(self, series_version: str) -> List[str]:
        """Retourne la liste des textes contenus dans *data/chunks/chunks_<series_version>/*.txt*"""
        # d = self.extracted_dir / f"chunks_{series_version}"
        d = os.path.normpath(os.path.join(self.extracted_dir, f"chunks_{series_version}"))
        d = Path(d)
        if not d.exists():
            raise FileNotFoundError(f"Répertoire introuvable : {d}")
        files = sorted(d.glob("*.txt"))
        if not files:
            raise RuntimeError("Aucun chunk trouvé dans le dossier : " + d.as_posix())
        return [p.read_text(encoding="utf-8") for p in files]

    # ------------------------------------------------------------------
    def build_from_text(self, text: str) -> int:
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
    
    # ------------------------------------------------------------------
    def build_from_series(self, series_version: str) -> dict:
        """
        Construit le KG à partir des chunks au lieu du fichier texte d'origine.
        """
        texts = self._load_series_texts(series_version)
        return self.build_from_chunks(texts)
    
    # def build_from_series(self, series_version: str) -> dict:
    #     series_version = f"serie_{series_version}"
    #     dir_path = os.path.normpath(os.path.join(self.extracted_dir, series_version))
    #     # dir_path = Path(os.path.join(self.extracted_dir, f"serie_{series_version}"))
    #     print(f"Chemin vérifié : {dir_path}")
    #     dir_path = Path(dir_path)
    #     if not dir_path.exists():
    #         print(f"Le répertoire n'existe pas : {dir_path}")
    #         return {"status": 404, "message": "Répertoire absent : " + dir_path.as_posix()}
        
    #     txt_files = sorted(Path(dir_path).glob("*.txt"))
    #     if not txt_files:
    #         return {"status": 404, "message": "Aucun fichier .txt dans " + os.path.abspath(dir_path)}

    #     full_text = "\n".join(p.read_text(encoding='utf-8') for p in txt_files)

        # triplets = self.build_from_text(full_text)
        # return {"triplets_created": triplets, "files_used": [p.name for p in txt_files]}

    # ------------------------------------------------------------------
    def build_from_chunks(self, chunks: list[str]) -> dict:
        """
        Construit le KG à partir des chunks au lieu du fichier texte d'origine.
        """
        full_text = "\n".join(chunks)
        if not full_text.strip():
            raise ValueError("Input text for relation extraction is empty.")
        
        triplets = self.build_from_text(full_text)
        return {"triplets_created": triplets, "chunks_used": len(chunks)}
                
    # ------------------------------------------------------------------
    def check_kg_exists(self) -> bool:
        """
        Retourne True si **au moins un nœud du KG** est présent
        dans la base configurée.
        """
        cypher = """
        MATCH (n)
        WHERE any(lbl IN labels(n)            // Option : filtrer vos labels KG
                  WHERE lbl IN ['Chunk','Entity','Document'])
        RETURN COUNT(n) > 0 AS exists
        """
        with self.driver.session(database=self.db) as s:   # <- session sur Addoha2
            return s.run(cypher).single()["exists"]
    
    