# app/api/v1/config.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Optional
from embedding import embedder_base
from embedding import embedding_manager
from embedding import embedding_pipeline
from embedding.embedder_base import HuggingFaceEmbedder, OpenAIEmbedder, GeminiEmbedder
from pydantic import BaseModel
import os, json

from .schemas import (         # met tes Pydantic ici si besoin
    EmbedderConfigResponse, EmbedderSelect
)

router = APIRouter(prefix="/config", tags=["Config"])

# Route pour configurer un embedder (si besoin d'une API externe)
# Route pour sélectionner un embedder valable
# Route pour changer la configuration de la base de données Neo4j
# Route pour redemarer le serveur MCP inclut
# Route pour changer la configuration du serveur MCP (sse/stdio, adresse, port, etc.)


@router.post("/embedder")
async def select_embedder(body: EmbedderSelect):
    # Stocker la conf dans un fichier ou base selon vos besoins
    try:
        with open(".embedder_cfg.json", "w", encoding="utf-8") as f:
            json.dump({"provider": body.provider, "params": body.params}, f)
        return {"selected": body.provider}
    except Exception as e:
        raise HTTPException(500, str(e))