import logging, sys, time, uuid, contextvars
import structlog

request_id_var = contextvars.ContextVar("request_id", default="-")

def _get_request_id(_, __, event_dict):
    event_dict["request_id"] = request_id_var.get()
    return event_dict

def setup_logging(level="INFO"):
    structlog.configure(
        processors=[
            _get_request_id,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level)),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
    )

def get_logger(name: str = "app"):
    return structlog.get_logger(name)

def log_step(name: str):
    log = get_logger(name)
    def decorator(fn):
        def wrapper(*args, **kwargs):
            t0 = time.perf_counter()
            log.info("start", step=name)
            try:
                res = fn(*args, **kwargs)
                log.info("end", step=name, elapsed_ms=int((time.perf_counter()-t0)*1000))
                return res
            except Exception as e:
                log.error("error", step=name, error=str(e))
                raise
        return wrapper
    return decorator
