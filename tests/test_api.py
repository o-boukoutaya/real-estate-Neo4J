import sys
import types
import pathlib
import pytest

pytest.importorskip('fastapi')

# ensure backend package on path
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'backend'))

# minimal stubs for heavy dependencies before importing routers
pydantic_mod = types.ModuleType('pydantic')
class BaseModel: ...
pydantic_mod.BaseModel = BaseModel
sys.modules.setdefault('pydantic', pydantic_mod)

embedding_pkg = types.ModuleType('embedding')
embedder_base = types.ModuleType('embedding.embedder_base')
embedder_base.HuggingFaceEmbedder = object
embedder_base.OpenAIEmbedder = object
embedder_base.GeminiEmbedder = object
embedding_manager_mod = types.ModuleType('embedding.embedding_manager')
class EmbeddingManager: ...
embedding_manager_mod.EmbeddingManager = EmbeddingManager
vector_store_mod = types.ModuleType('embedding.vector_store')
class Neo4jVectorManager:
    def __init__(self, *args, **kwargs):
        pass
    def test_connection(self):
        return True
vector_store_mod.Neo4jVectorManager = Neo4jVectorManager
embedding_pipeline = types.ModuleType('embedding.embedding_pipeline')
embedding_pkg.embedder_base = embedder_base
embedding_pkg.embedding_manager = embedding_manager_mod
embedding_pkg.vector_store = vector_store_mod
embedding_pkg.embedding_pipeline = embedding_pipeline
sys.modules['embedding'] = embedding_pkg
sys.modules['embedding.embedder_base'] = embedder_base
sys.modules['embedding.embedding_manager'] = embedding_manager_mod
sys.modules['embedding.vector_store'] = vector_store_mod
sys.modules['embedding.embedding_pipeline'] = embedding_pipeline

knowledge_pkg = types.ModuleType('knowledge')
graph_builder = types.ModuleType('knowledge.graph_builder')
class GraphBuilder: ...
graph_builder.GraphBuilder = GraphBuilder
schema_manager = types.ModuleType('knowledge.schema_manager')
class GraphSchemaManager: ...
schema_manager.GraphSchemaManager = GraphSchemaManager
kg_builder = types.ModuleType('knowledge.kg_builder')
class KGBuilder:
    def __init__(self, *args, **kwargs):
        pass
    def check_kg_exists(self):
        return True
kg_builder.KGBuilder = KGBuilder
knowledge_pkg.graph_builder = graph_builder
knowledge_pkg.schema_manager = schema_manager
knowledge_pkg.kg_builder = kg_builder
sys.modules['knowledge'] = knowledge_pkg
sys.modules['knowledge.graph_builder'] = graph_builder
sys.modules['knowledge.schema_manager'] = schema_manager
sys.modules['knowledge.kg_builder'] = kg_builder

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api import api_router

def test_status_api_endpoint():
    app = FastAPI()
    app.include_router(api_router)
    client = TestClient(app)
    resp = client.get('/api/v1/status/api')
    assert resp.status_code == 200
    assert resp.json() == {'ok': True}
