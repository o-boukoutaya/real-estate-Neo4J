# main.py ─ version lifespan (FastAPI ≥ 0.111)
import os
import asyncio
from contextlib import asynccontextmanager
import contextlib
from dotenv import load_dotenv

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.wsgi import WSGIMiddleware

# from app.router import router as api_router
from app.api import api_router
from tools.graph_rag_tool import mcp as mcp_app
from settings import SERVER_OPTIONS

load_dotenv()

# ──────────────────────────────────────────────────────────────
# Lifespan FastAPI : gère start-/shutdown de MCP
# ──────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    transport = SERVER_OPTIONS.get("transport", "http")
    # START-UP
    if transport == "stdio":
        # Lancer run_stdio_async en tâche de fond
        app.state.mcp_task = asyncio.create_task(mcp_app.run_stdio_async())
    if transport == "sse":
        # Lancer run_stdio_async en tâche de fond
        app.state.mcp_task = asyncio.create_task(mcp_app.run_sse_async())

    yield  # —— l’application tourne ——

    # SHUT-DOWN
    if transport in {"sse", "stdio"}:
        app.state.mcp_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await app.state.mcp_task

# ──────────────────────────────────────────────────────────────
# FastAPI app racine
# ──────────────────────────────────────────────────────────────

# Montage des sous-applications
sub_app = mcp_app.http_app()
# sub_app = mcp_app.streamable_http_app()


app = FastAPI(
    title="GraphRAG Admin + MCP",
    lifespan=sub_app.router.lifespan_context,
    # lifespan=lifespan
)

# Health-check
@app.get("/healthz", include_in_schema=False)
async def healthz():
    return JSONResponse({"status": "ok"})

app.mount("/mcp-server", sub_app, "mcp")     # routes MCP (SSE/JSON)

# app.include_router(api_router, prefix="/api")         # routes API
app.include_router(api_router) 

# Handler d'exception global pour toujours renvoyer du JSON
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)}
    )

# ──────────────────────────────────────────────────────────────
# Uvicorn entry-point
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    # uvicorn.run(
    #     "main:app",
    #     host=SERVER_OPTIONS["host"],
    #     port=SERVER_OPTIONS["port"],
    #     log_level="info",
    #     reload=bool(os.getenv("DEV_RELOAD", False)),
    # )
    uvicorn.run("main:app", host=SERVER_OPTIONS["host"], port=SERVER_OPTIONS["port"], reload=True)


# Points clés
# MCP dans FastAPI Accessible sur le port 8050
# → POST http://127.0.0.1:8050/mcp-server/run
# → GET http://127.0.0.1:8050/mcp-server/events

# second serveur SSE Dans ce serveur dédié, le sous-app est à la racine
# → POST http://127.0.0.1:8443/run
# → GET http://127.0.0.1:8443/events
# (le préfixe /mcp n’existe pas sur 8443)


# UVicorn
# │
# ├── /api/*          (FastAPI)      → Vue3
# ├── /mcp/run        (HTTP POST)    → tests manuels / debug
# ├── /mcp/events     (SSE GET)      → Multi-Agent (stream)
# └──  STDIO loop     (background)   → Multi-Agent CLI