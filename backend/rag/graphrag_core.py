# backend/rag/graphrag_core.py
from neo4j import GraphDatabase
from embedding.embedding_manager import EmbeddingManager
from embedding.vector_store import Neo4jVectorManager
from rag.retriever import Retriever
from rag.query_generator import QueryGenerator
from rag.answer_synthesizer import AnswerSynthesizer
from rag.context_manager import ContextManager


class GraphRAG:
    def __init__(self, neo4j_cfg: dict, embed_cfg: dict | None = None, llm_cfg: dict | None = None):
        # ----- Injection de dépendances -------------------------------
        self.embedder = EmbeddingManager(**(embed_cfg or {"provider": "huggingface"}))
        self.vstore = Neo4jVectorManager(**neo4j_cfg)
        self.driver = GraphDatabase.driver(
            neo4j_cfg["url"], auth=(neo4j_cfg["username"], neo4j_cfg["password"])
        )

        self.retriever = Retriever(self.embedder, self.vstore, self.driver)
        self.qgen = QueryGenerator()
        self.synth = AnswerSynthesizer()
        self.ctx_mgr = ContextManager()

    # ------------------------------------------------------------------
    def query(self, question: str, *, k: int = 8) -> dict:
        hits = self.retriever.retrieve(question, k=k)
        context = self.ctx_mgr.merge(**hits)

        # (option) : générer + exécuter une requête Cypher supplémentaire
        ents = self.retriever._extract_entities([question])
        cypher = self.qgen.generate(question, ents)

        answer = self.synth.synthesize(context=context, question=question)
        return {
            "answer": answer,
            "context": hits,
            "cypher": cypher,
        }
