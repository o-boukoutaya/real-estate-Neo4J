from fastapi import APIRouter
from .v1 import api_v1_router

api_router = APIRouter(prefix="/api")
api_router.include_router(api_v1_router, prefix="/v1")
