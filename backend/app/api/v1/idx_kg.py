from settings import NEO4J_CFG  # ← mon dict centralisé
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os, json
from pathlib import Path

from .schemas import (         # met tes Pydantic ici si besoin
    SeriesIndexRequest, KGRequest
)

from embedding.embedding_manager import EmbeddingManager
from embedding.Embedding_config import EmbeddingConfig
from embedding.embedding_pipeline import EmbeddingPipeline
from embedding.vector_store import Neo4jVectorManager
from knowledge.kg_builder import KGBuilder
from knowledge.schema_manager import GraphSchemaManager

from knowledge.graph_builder import GraphBuilder  # depuis repo Neo4j Labs

router = APIRouter(prefix="/idx-kg", tags=["Indexing&KG"])
# database_name = os.getenv("NEO4J_DATABASE", "addoha2") 

_DEF_CFG = Path(".embedder_cfg.json")

def _load_default():
    if _DEF_CFG.exists():
        return json.loads(_DEF_CFG.read_text())
    return {"provider": "huggingface", "params": {}}

# -------------------------------------------------------------------
@router.post("/create-idx") # (POST) http://localhost:8050/api/v1/idx-kg/create-idx
async def create_index(req: SeriesIndexRequest):
    try:
        cfg = _load_default() if req.embedder is None else {"provider": req.embedder, "params": {}}
        # mgr = EmbeddingManager(cfg["provider"], **cfg.get("params", {}))
        mgr = EmbeddingManager(EmbeddingConfig(**cfg))
        store = Neo4jVectorManager(**NEO4J_CFG)
        pipeline = EmbeddingPipeline(embedder=mgr, vector_store=store)
        results = pipeline.get_chunks_text(req.series)
        if results["status"] == "error":
            return results
        r = pipeline.run_from_series(results["chunks"], req.series)
        return r
        # return {"index": store.index_name, "chunks_indexed": n_chunks, "embedder": cfg["provider"]}

    except (FileNotFoundError, RuntimeError) as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "OK"}
    # try:
    #     cfg = _load_default() if req.embedder is None else {"provider": req.embedder, "params": {}}
    #     mgr = EmbeddingManager(cfg["provider"], **cfg.get("params", {}))

    #     # idx_name = f"index_{req.series}"
    #     store = Neo4jVectorManager(**NEO4J_CFG) # , index_name=idx_name
    #     # if not store.check_index_exists():
    #     #     store.create_index(dim=req.dim or 768)
        
    #     # kg_builder = KGBuilder(driver=store.driver, database=store.db, llm=GraphBuilder(), schema_manager=GraphSchemaManager())
    #     # Vérifier si un KG existe
    #     # if not kg_builder.check_kg_exists():
    #         # return {"status": "error", "message": "Aucun KG dans la base de données "+store.db}
        
    #     pipeline = EmbeddingPipeline(embedder=mgr, vector_store=store)
    #     results = pipeline.get_chunks_text(req.series)
    #     if results["status"] == "error":
    #         return results
    #     # n_chunks = pipeline.run_from_series(req.series)
    #     # return {"index": store.index_name, "chunks_indexed": n_chunks, "embedder": cfg["provider"]}
    #     return {"status": "OK"}
    # except (FileNotFoundError, RuntimeError) as e:
    #     raise HTTPException(404, str(e))
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------------
@router.post("/build-kg") # (POST) http://localhost:8050/api/v1/idx-kg/build-kg
async def build_kg(body: KGRequest):
    store = Neo4jVectorManager(**NEO4J_CFG)
    llm_chain = GraphBuilder()  # config LLM selon ton choix (OpenAI, Gemini…)
    kg = KGBuilder(driver=store.driver, database=store.db, llm=llm_chain, schema_manager=GraphSchemaManager())
    results = kg.build_from_series(body.series)
    return results