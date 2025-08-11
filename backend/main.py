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
# Lifespan FastAPI : (for stdio/SSE background if needed) — not used when mounting SSE app
# ──────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    transport = SERVER_OPTIONS.get("transport", "http")
    # START-UP
    if transport == "stdio":
        # Optional: run stdio transport in background (not used when mounting SSE app)
        app.state.mcp_task = asyncio.create_task(mcp_app.run_stdio_async())
    # For SSE, we'll mount the Starlette sub-app instead of spawning a separate server.

    yield  # —— l’application tourne ——

    # SHUT-DOWN
    if transport in {"sse", "stdio"}:
        app.state.mcp_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await app.state.mcp_task

# ──────────────────────────────────────────────────────────────
# FastAPI app racine
# ──────────────────────────────────────────────────────────────

# Montage des sous-applications (FastMCP SSE ASGI app)
sub_app = mcp_app.sse_app()


app = FastAPI(
    title="GraphRAG Admin + MCP",
    lifespan=sub_app.router.lifespan_context,
)

# Health-check
@app.get("/healthz", include_in_schema=False)
async def healthz():
    return JSONResponse({"status": "ok"})

app.mount("/mcp-server", sub_app, "mcp")     # routes MCP (SSE under /mcp-server)

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
    uvicorn.run("main:app", host=SERVER_OPTIONS["host"], port=SERVER_OPTIONS["port"], reload=True)


# Points clés
# MCP dans FastAPI Accessible sur le port 8050
# With fastmcp.sse_app():
# → GET  http://127.0.0.1:8050/mcp-server/sse
# → POST http://127.0.0.1:8050/mcp-server/messages/

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