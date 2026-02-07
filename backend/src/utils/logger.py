# backend/src/core/logger.py
import logging
import functools
from datetime import datetime
from typing import Callable, Any
import inspect
import sys

# Configure the root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # To console
        logging.FileHandler("backend/logs/app.log"),  # To file
    ],
)

logger = logging.getLogger(__name__)


def log(func: Callable) -> Callable:
    """
    Decorator for logging function calls.

    Logs:
    - Function execution start
    - Function arguments (optional)
    - Successful completion
    - Errors
    - Execution time

    Usage:
    @log
    async def my_function(arg1, arg2):
        ...
    """

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        return await _log_wrapper(func, *args, **kwargs)

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        return _log_wrapper(func, *args, **kwargs)

    def _log_wrapper(func: Callable, *args, **kwargs) -> Any:
        start_time = datetime.now()

        # Log the call
        logger.info(
            f"START {func.__module__}.{func.__name__} "
            f"args={args if len(args) < 3 else '(...)'} "
            f"kwargs={kwargs if len(str(kwargs)) < 100 else '(...)'}"
        )

        try:
            # Execute the function
            result = func(*args, **kwargs)

            # Log success
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.info(
                f"SUCCESS {func.__module__}.{func.__name__} "
                f"duration={duration:.3f}s"
            )

            return result

        except Exception as e:
            # Log the error
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.error(
                f"ERROR {func.__module__}.{func.__name__} "
                f"duration={duration:.3f}s "
                f"error={type(e).__name__}: {str(e)}",
                exc_info=True,  # Full traceback
            )
            raise  # Re-raise the error

    # Return the appropriate wrapper based on the function type
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


def log_database_queries(func: Callable) -> Callable:
    """Decorator for logging SQL queries"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"DATABASE {func.__name__} called")
        return func(*args, **kwargs)

    return wrapper
