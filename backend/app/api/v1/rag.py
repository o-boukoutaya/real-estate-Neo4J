from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from pathlib import Path
import os
# from app.rag.graphrag_core import GraphRAG
# http://127.0.0.1:8050/docs#/Diag sur navigateur


from mcp.server.fastmcp import Context
from tools.graph_rag_tool import search_data   # même fonction que pour MCP

router = APIRouter(prefix="/diag", tags=["Diag"])

class QueryIn(BaseModel):
    question: str

# @router.post("/query")
# def query(req: QueryIn, rag: GraphRAG = Depends(GraphRAG)):
#     return rag.query(req.question)


@router.post("/search") # (POST) http://localhost:8050/api/v1/rag/diag/search
async def diag_search(q: str, k: int = 8):
    try:
        ctx = Context(client_id="diag")          # contexte bidon
        answer = await search_data(ctx, q, k)    # appel direct
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(500, str(e))
