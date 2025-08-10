"""Pipeline : ingestion de chunks (en mémoire **ou** depuis un dossier) → embeddings → Neo4j vector store.
    La route FastAPI ne fait qu'orchestrer ; toute la logique se trouve ici.
"""
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

from .embedding_manager import EmbeddingManager
from .vector_store import Neo4jVectorManager

class EmbeddingPipeline:
    def __init__(self, *, embedder: EmbeddingManager, vector_store: Neo4jVectorManager,
                 data_root: Path = Path("data/chunks")):
        self.embedder = embedder
        self.vector_store = vector_store
        self.data_root = data_root

    # ------------------------------------------------------------------
    def _load_series_texts(self, series_version: str) -> List[str]:
        """Retourne la liste des textes contenus dans *data/chunks/chunks_<series_version>/*.txt*"""
        d = self.data_root / f"chunks_{series_version}"
        if not d.exists():
            raise FileNotFoundError(f"Répertoire introuvable : {d}")
        files = sorted(d.glob("*.txt"))
        if not files:
            raise RuntimeError("Aucun chunk trouvé dans le dossier : " + d.as_posix())
        return [p.read_text(encoding="utf-8") for p in files]

    # ------------------------------------------------------------------
    def run(self, chunks: List[Dict], *, version: str | None = None):
        """Ingère une liste de dictionnaires : {"text": …}."""
        texts = [c["text"] for c in chunks]
        embeddings = self.embedder.embed_texts(texts)
        if not self.vector_store.check_index_exists():
            dim = len(embeddings[0])
            self.vector_store.create_index(dim=dim)
        self.vector_store.save(texts=texts, embeddings=embeddings, version=version)
        return len(chunks)

    def get_chunks_text(self, series_version: str) -> List[str]:
        """Retourne les textes des chunks d’une série."""
        texts = self._load_series_texts(series_version)
        if not texts:
            return {"status": "error", "message": f"Série vide : {series_version}"}
        return {"status":"ok", "chunks": texts} 
    # ------------------------------------------------------------------
    # def run_from_series(self, series_version: str, *, version: str | None = None):
    #     """Charge automatiquement tous les chunks d’une série puis appelle *run()*."""
    #     texts = self._load_series_texts(series_version)
    #     dicts = [{"text": t} for t in texts]
    #     return self.run(dicts, version=version or series_version)
    # ------------------------------------------------------------------

    def run_from_series(self, texts: List[str], series_version: str, *, similarity: str = "cosine") -> int:
        """
        Ingeste une série (texte → chunks → embeddings → Neo4j).

        Parameters
        ----------
        series_version : str
            Identifiant de la série (ex. "110625-022017").
        version : str, optional
            Tag stocké dans le nœud ; défaut = series_version.
        similarity : str, optional
            Fonction de similarité de l’index vectoriel
            ("cosine", "euclidean", "dotproduct").
        Returns
        -------
        int
            Nombre de chunks réellement indexés.
        """

        # 1. Préparer les données ------------------------------------------------
        embeddings: List[List[float]] = self.embedder.embed_texts(texts)
        dim: int = len(embeddings[0])
        
        # 2. Créer l’index vectoriel (une seule fois) ----------------------------
        if not self.vector_store.check_index_exists():
            self.vector_store.create_index(dim=dim, similarity=similarity)
        
        # 3. Transformer en lignes batch ----------------------------------------
        stamp = datetime.now().isoformat(timespec="seconds")
        rows: List[Dict[str, Any]] = [
            {
                "cid": f"{series_version}-{i:06d}",
                "text": txt,
                "vec":  vec,
                "series": series_version,
                "ingest_ts": stamp,
            }
            for i, (txt, vec) in enumerate(zip(texts, embeddings), 1)
        ]

        # 4. Insérer / mettre à jour les nœuds Chunk + vecteur -------------------
        cypher_chunks = """
            UNWIND $rows AS row
            MERGE (c:Chunk {id: row.cid})
            ON CREATE SET
                    c.text        = row.text,   
                    c.embedding   = row.vec,
                    c.series      = row.series,
                    c.ingest_ts   = row.ingest_ts
            ON MATCH SET
                    c.text        = row.text,
                    c.embedding   = row.vec,
                    c.series      = row.series
            """
        
        with self.vector_store.driver.session(database=self.vector_store.db) as s:
            s.run(cypher_chunks, rows=rows)
            
            # 5. Relations NEXT_CHUNK (séquencement) ---------------------------
            rels = [
                {"from": rows[i]["cid"], "to": rows[i + 1]["cid"]}
                for i in range(len(rows) - 1)
            ]
            if rels:
                cypher_rels = """
                UNWIND $rels AS rel
                MATCH (c1:Chunk {id: rel.from})
                MATCH (c2:Chunk {id: rel.to})
                MERGE (c1)-[:NEXT_CHUNK]->(c2)
                """
                s.run(cypher_rels, rels=rels)

        return len(rows)