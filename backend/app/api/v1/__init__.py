from fastapi import APIRouter

from .ingestion import router as ingestion_router
from .rag       import router as rag_router
from .status    import router as status_router  # /status
from .config    import router as config_router
from .idx_kg    import router as idx_kg_router

api_v1_router = APIRouter()
api_v1_router.include_router(status_router)
api_v1_router.include_router(rag_router,       prefix="/rag")
api_v1_router.include_router(ingestion_router)
api_v1_router.include_router(config_router)
api_v1_router.include_router(idx_kg_router)
