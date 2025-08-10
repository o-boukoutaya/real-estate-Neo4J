import sys
import types
import pathlib
import pytest

# Add backend to path
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'backend'))

# Stub embedding manager and vector store before importing Retriever
embedding_pkg = types.ModuleType('embedding')
embedding_manager_mod = types.ModuleType('embedding.embedding_manager')
class FakeEmbeddingManager:
    def __init__(self, *args, **kwargs):
        pass
    def embed_texts(self, texts):
        return [[0.1, 0.2, 0.3] for _ in texts]
embedding_manager_mod.EmbeddingManager = FakeEmbeddingManager
vector_store_mod = types.ModuleType('embedding.vector_store')
class FakeVectorStore:
    def __init__(self, *args, **kwargs):
        pass
    def search_similar(self, embedding, k=5):
        return [{'score': 0.9, 'text': 'Alice met Bob.'}]
vector_store_mod.Neo4jVectorManager = FakeVectorStore
embedding_pkg.embedding_manager = embedding_manager_mod
embedding_pkg.vector_store = vector_store_mod
sys.modules['embedding'] = embedding_pkg
sys.modules['embedding.embedding_manager'] = embedding_manager_mod
sys.modules['embedding.vector_store'] = vector_store_mod

# stub neo4j driver and type
neo4j_mod = types.ModuleType('neo4j')
class Driver: ...
class GraphDatabase:
    @staticmethod
    def driver(url, auth):
        return object()
neo4j_mod.Driver = Driver
neo4j_mod.GraphDatabase = GraphDatabase
sys.modules['neo4j'] = neo4j_mod

from rag.retriever import Retriever

class DummySession:
    def run(self, cypher, ents):
        return [{'name': 'Alice', 'labels': ['Person']}]
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        pass

class DummyDriver:
    def session(self):
        return DummySession()

@pytest.fixture
def retriever():
    embedder = FakeEmbeddingManager()
    vstore = FakeVectorStore()
    driver = DummyDriver()
    return Retriever(embedder, vstore, driver)

def test_retrieve_combines_sources(retriever):
    result = retriever.retrieve('Who is Alice?')
    assert result['vector_hits'][0]['text'] == 'Alice met Bob.'
    assert result['cypher_hits'][0]['name'] == 'Alice'
