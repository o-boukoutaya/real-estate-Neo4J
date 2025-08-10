from fastapi import APIRouter
from ingestion_routes import router as ingestion_router

# Central router manager
routes_manager = APIRouter()

# Include modular routes
routes_manager.include_router(ingestion_router, prefix="/ingestion")
