"""Driver Neo4j 5 – vector index (cosine)."""
from typing import List, Dict
from neo4j import GraphDatabase
import os

class Neo4jVectorManager:
    def __init__(self, *, url: str, username: str, password: str, database: str | None = None,#, neo4j_cfg: dict
                 index_name: str = "chunkVector", node_label: str = "Chunk",
                 text_prop: str = "text", embed_prop: str = "embedding", version_prop: str = "version"):
        self.driver     = GraphDatabase.driver(url, auth=(username, password))
        # self.driver     = GraphDatabase.driver(
        #     neo4j_cfg["url"], auth=(neo4j_cfg["username"], neo4j_cfg["password"], neo4j_cfg["database"])
        # )
        self.db         =  database # or os.getenv("NEO4J_DATABASE", "neo4j") # neo4j_cfg["database"]
        self.index_name = index_name
        self.node_label = node_label
        self.text_prop  = text_prop
        self.embed_prop = embed_prop
        self.version_prop = version_prop
    
    # ---------------------- utils ----------------------
    @staticmethod
    def _sanitize(name: str) -> str:
        """Remplace les caractères non autorisés pour un identifiant Neo4j."""
        import re
        return re.sub(r"[^A-Za-z0-9_]", "_", name)

    # ---------------------- meta ----------------------
    def test_connection(self) -> bool:
        with self.driver.session(database=self.db) as s:
            return bool(s.run("RETURN 1").single()[0])

    def check_index_exists(self) -> bool:
        q = "SHOW INDEXES YIELD name WHERE name = $name RETURN count(*) AS c"
        with self.driver.session(database=self.db) as s:
            return s.run(q, name=self._sanitize(self.index_name)).single()["c"] > 0

    def create_index(self, dim: int = 768, similarity: str = "cosine"):
        """Crée un vector index (Neo4j 5) en neutralisant les caractères invalides.
        Exemple de requête générée :
        CREATE VECTOR INDEX `index_110625_022017` IF NOT EXISTS
        FOR (c:Chunk) ON (c.embedding)
        OPTIONS { indexConfig: { `vector.dimensions`: 768, `vector.similarity_function`: 'cosine' } }
        """
        safe_name = self._sanitize(self.index_name)
        q = (
            f"CREATE VECTOR INDEX `{safe_name}` IF NOT EXISTS "
            f"FOR (c:{self.node_label}) ON (c.{self.embed_prop}) "
            f"OPTIONS {{ indexConfig: {{ `vector.dimensions`: {dim}, "
            f"`vector.similarity_function`: '{similarity}' }} }}"
        )
        with self.driver.session(database=self.db) as s:
            s.run(q)

    # ---------------------- CRUD ----------------------
    def save(self, *, texts: List[str], embeddings: List[List[float]], version: str | None = None,
             metadatas: List[Dict] | None = None):
        rows = []
        for i, (t, e) in enumerate(zip(texts, embeddings)):
            row = {self.text_prop: t, self.embed_prop: e}
            if version:
                row[self.version_prop] = version
            if metadatas and i < len(metadatas):
                row.update(metadatas[i])
            rows.append(row)
        query = (
            f"UNWIND $rows AS r CREATE (c:{self.node_label}) SET c = r"
        )
        with self.driver.session(database=self.db) as s:
            s.run(query, rows=rows)

    def search_similar(self, embedding: List[float], k: int = 5):
        q = (
            f"CALL db.index.vector.queryNodes('{self.index_name}', $k, $vec) "
            "YIELD node, score RETURN node, score"
        )
        with self.driver.session(database=self.db) as s:
            return [{"score": r["score"], "text": r["node"][self.text_prop]} for r in s.run(q, k=k, vec=embedding)]