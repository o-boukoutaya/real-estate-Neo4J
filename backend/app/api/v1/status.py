# app/api/v1/ingestion.py
from settings import NEO4J_CFG  # ← mon dict centralisé
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Optional
from embedding import embedder_base
from embedding.embedding_manager import EmbeddingManager
from embedding.vector_store import Neo4jVectorManager
import os

from knowledge.graph_builder import GraphBuilder
from knowledge.schema_manager import GraphSchemaManager
from knowledge.kg_builder import KGBuilder
from embedding import embedding_pipeline
from embedding.embedder_base import HuggingFaceEmbedder, OpenAIEmbedder, GeminiEmbedder
from pydantic import BaseModel


from .schemas import (         # met tes Pydantic ici si besoin
    EmbedderConfigResponse,
)

router = APIRouter(prefix="/status", tags=["Status"])
# database_name = os.getenv("NEO4J_DATABASE", "addoha2") 

@router.get("/api") # (GET) http://localhost:8050/api/v1/status/api
async def api_health():
    return {"ok": True}

# Route pour voir les embedders supportés par le système et leurs status (valable ou non)
# Route pour voir l'embedder active (sont statut)
# Route pour voir le status de connexion avec la base de données Neo4j (connecté ou non)
# Route pour vérifier l'existance d'un Knowledge Graph (et son statut)
# Route pour vérifier l'existance d'un index ou la base est vide

# Route pour voir le status de l'API
# Route pour voir le statut du Serveur MCP (démarré ou non)
# Route pour voir la connexion avec un client MCP (en cours ou non)
# Notificateur des communications (Q/A) entre le client et le serveur MCP
# Route pour  voir les informations sur le client MCP


@router.get("/neo4j-cnx") # (GET) http://localhost:8050/api/v1/status/neo4j-cnx
async def neo4j_status():
    store = Neo4jVectorManager(**NEO4J_CFG)
    try:
        connected = store.test_connection()
        return {"connected": connected, "to": store.db}
    except Exception as e:
        raise HTTPException(500, str(e))
    
# -------------------------------------------------------------------

@router.get("/neo4j-idx") # (GET) http://localhost:8050/api/v1/status/neo4j-idx
async def neo4j_indexes():
    """Retourne **tout** le catalogue d’index + sous‑liste VECTOR pour diagnostic."""
    store = Neo4jVectorManager(**NEO4J_CFG)
    try:
        with store.driver.session(database=store.db) as s:
            rows = s.run("SHOW INDEXES YIELD name, type, entityType, state RETURN name, type, entityType, state").data()
        vec_only = [r for r in rows if r["type"].upper().startswith("VECTOR")]
        return {"vector_indexes": vec_only}#, "all_indexes": rows}
    except Exception as e:
        raise HTTPException(500, str(e))
    # except Exception as e:
    #     raise HTTPException(500, str(e))(500, str(e))

@router.get("/neo4j-idx-name") # (GET) http://localhost:8050/api/v1/status/neo4j-idx-name
async def neo4j_indexe_name():
    """Retourne **tout** le catalogue d’index + sous‑liste VECTOR pour diagnostic."""
    store = Neo4jVectorManager(**NEO4J_CFG)
    try:
        with store.driver.session(database=store.db) as s:
            row = s.run("SHOW INDEXES YIELD name, type, entityType, labelsOrTypes, properties WHERE type = 'VECTOR'").data()
        return {"default_index_name": row[0]['name']}
    except Exception as e:
        raise HTTPException(500, str(e))
    # except Exception as e:
    #     raise HTTPException(500, str(e))(500, str(e))

# -------------------------------------------------------------------

@router.get("/neo4j-kg") # (GET) http://localhost:8050/api/v1/status/neo4j-kg
async def neo4j_kgExists():
    """Retourn si dans la base de données Neo4j il existe un Knowledge Graph."""
    
    store = Neo4jVectorManager(**NEO4J_CFG)

    kg_builder = KGBuilder(driver=store.driver, database=store.db, llm=GraphBuilder(), schema_manager=GraphSchemaManager())
    try:
        # Vérifier si un KG existe
        if not kg_builder.check_kg_exists():
            return {"status": "error", "message": "Aucun KG dans la base de données "+store.db}
        return {"kg_exists": True}
    except Exception as e:
        raise HTTPException(500, str(e))

# -------------------------------------------------------------------

@router.get("/embedders")
async def embedders_status():
    provs = ["huggingface", "openai", "gemini"]
    statuses = {}
    for p in provs:
        try:
            mgr = EmbeddingManager(p)
            mgr.validate()
            statuses[p] = "ready"
        except Exception:
            statuses[p] = "error"
    return statuses