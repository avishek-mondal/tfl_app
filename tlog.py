import structlog
from structlog.stdlib import BoundLogger

# tfl app logger - tlog

_global_logger: BoundLogger = structlog.get_logger('root_tlog')


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
