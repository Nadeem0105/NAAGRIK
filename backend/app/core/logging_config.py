import contextvars
import logging
import sys
import structlog

# Context variables for tracing request lifecycle
request_id_ctx = contextvars.ContextVar("request_id", default=None)
user_id_ctx = contextvars.ContextVar("user_id", default=None)


def add_tracing_ctx(logger, method_name, event_dict):
    """Automatically append tracing variables from ContextVars to all structured logs."""
    req_id = request_id_ctx.get()
    u_id = user_id_ctx.get()
    
    if req_id:
        event_dict["request_id"] = req_id
    if u_id:
        event_dict["user_id"] = str(u_id)
        
    return event_dict


def setup_logging():
    """Setup structlog configuration."""
    # Standard Python logging configuration
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )
    
    # Pre-processors for structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        add_tracing_ctx,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    # Output format (JSON for production, ConsoleRenderer for development)
    # We will format as JSON for structure
    processors.append(structlog.processors.JSONRenderer())
    
    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
