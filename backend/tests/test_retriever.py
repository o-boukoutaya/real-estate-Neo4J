from rag.retriever import Retriever

class DummyEmbedder:
    def embed_texts(self, texts): return [[0.1, 0.2]]

class DummyStore:
    def search_similar(self, vec, k): return [{"text":"Doc A"}]

def test_retrieve_basic():
    r = Retriever(DummyEmbedder(), DummyStore(), None)
    res = r.retrieve("hello")
    assert "vector_hits" in res
