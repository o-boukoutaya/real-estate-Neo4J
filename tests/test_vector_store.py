import sys
import types
import pathlib
from unittest.mock import MagicMock
import pytest

# ensure backend modules are used, not previous stubs
sys.modules.pop('embedding', None)
sys.modules.pop('embedding.vector_store', None)

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'backend'))

class DummySession:
    def __init__(self):
        self.run = MagicMock()
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        pass

class DummyDriver:
    def __init__(self, session):
        self._session = session
    def session(self, database=None):
        return self._session

if 'neo4j' not in sys.modules:
    neo4j = types.ModuleType('neo4j')
    class DummyGraphDatabase:
        @staticmethod
        def driver(url, auth):
            return DummyDriver(DummySession())
    neo4j.GraphDatabase = DummyGraphDatabase
    sys.modules['neo4j'] = neo4j

from embedding.vector_store import Neo4jVectorManager

@pytest.fixture
def manager():
    session = DummySession()
    driver = DummyDriver(session)
    mgr = Neo4jVectorManager(url='bolt://x', username='u', password='p')
    mgr.driver = driver
    return mgr, session

def test_save_builds_rows(manager):
    mgr, session = manager
    mgr.save(texts=['foo'], embeddings=[[0.1]], version='v1')
    session.run.assert_called_once()
    args, kwargs = session.run.call_args
    assert kwargs['rows'][0]['text'] == 'foo'
    assert kwargs['rows'][0]['embedding'] == [0.1]
    assert kwargs['rows'][0]['version'] == 'v1'

def test_search_similar_formats_results(manager):
    mgr, session = manager
    session.run.return_value = [{'score': 1.0, 'node': {'text': 'hello'}}]
    results = mgr.search_similar([0.1], k=1)
    assert results == [{'score': 1.0, 'text': 'hello'}]
