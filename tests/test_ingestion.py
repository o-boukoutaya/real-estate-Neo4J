import pathlib
import sys
import pytest

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'backend'))
from ingestion.chunker import Chunker

@pytest.fixture
def sample_file(tmp_path):
    version_dir = tmp_path / 'v1'
    version_dir.mkdir()
    file_path = version_dir / 'doc.txt'
    content = 'Hello world. This is a test.'
    file_path.write_text(content)
    return tmp_path, 'v1', 'doc', 'txt', content

def test_get_text_file_reads_content(sample_file):
    extracted_dir, version, fname, fext, content = sample_file
    chunker = Chunker(extracted_dir=str(extracted_dir))
    text = chunker.get_text_file(version, fname, fext)
    assert text == content

def test_character_split_generates_chunks():
    chunker = Chunker(chunk_size=10, chunk_overlap=0)
    text = 'abcdefghij1234567890'
    chunks = chunker.character_split(text)
    assert chunks == ['abcdefghij', '1234567890']
