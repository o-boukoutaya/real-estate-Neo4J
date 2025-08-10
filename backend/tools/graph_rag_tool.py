from mcp.server.fastmcp import Context # , FastMCP
from fastmcp import FastMCP
from rag.graphrag_core import GraphRAG
from settings import NEO4J_CFG  # ← mon dict centralisé
from typing import List, Dict
from settings import SERVER_OPTIONS
import json

# ──────────────────────────────────────────────────────────────
# MCP : initialisation (pas encore lié à HTTP)
# ──────────────────────────────────────────────────────────────

# mcp = FastMCP(
#     title = "GraphRAG",
#     description="GraphRAG MCP Server",
#     host=SERVER_OPTIONS["host"],
#     port=SERVER_OPTIONS["port_snd"]
# )

mcp = FastMCP()


rag_engine = GraphRAG(neo4j_cfg=NEO4J_CFG)


@mcp.tool()
async def search_data(ctx: Context, query: str, limit: int = 8) -> str:
# async def search_data(query: str, limit: int = 8) -> str:
    """
    Recherche sémantique + graphe sur le portefeuille immobilier.
    Args:
        query: question exprimée en langue naturelle
        limit: top-k passages vectoriels (par défaut : 8)
    """
    res = rag_engine.query(query, k=limit)
    return json.dumps(res, ensure_ascii=False, indent=2)
