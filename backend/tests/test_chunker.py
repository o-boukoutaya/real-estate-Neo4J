from ingestion.chunker import Chunker

def test_sentence_split():
    txt = "Bonjour. Je suis ici. Et toi ?"
    chunks = Chunker().sentence_split(txt)
    assert len(chunks) == 3
