import structlog
from structlog.stdlib import BoundLogger

_global_logger: structlog.stdlib.BoundLogger = structlog.get_logger('root_plog')


def info(*args, **kwargs):
    """Log message with level INFO."""
    return _global_logger.info(*args, **kwargs)


def debug(*args, **kwargs):
    """Log message with level DEBUG."""
    return _global_logger.debug(*args, **kwargs)


def warn(*args, **kwargs):
    """Log message with level WARNING."""
    return _global_logger.warn(*args, **kwargs)


def error(*args, **kwargs):
    """Log message with level ERROR."""
    return _global_logger.error(*args, **kwargs)
