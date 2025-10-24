# app/api/middleware.py
from starlette.middleware.base import BaseHTTPMiddleware
import uuid, time
from app.core.logging import request_id_var, get_logger

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        token = request_id_var.set(request.headers.get("x-request-id", str(uuid.uuid4())))
        log = get_logger("api")
        t0 = time.perf_counter()
        try:
            log.info("http.request", method=request.method, path=request.url.path)
            resp = await call_next(request)
            return resp
        finally:
            log.info("http.response", elapsed_ms=int((time.perf_counter()-t0)*1000))
            request_id_var.reset(token)
