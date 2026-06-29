import logging
import functools
from datetime import datetime
from typing import Callable, TypeVar, Awaitable, cast
from typing_extensions import ParamSpec
import inspect
import sys
from pathlib import Path

log_path = Path(__file__).parent.parent.parent / "logs" / "app.log"

# Configure the root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # To console
        logging.FileHandler(log_path),  # To file
    ],
)

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


def log(func: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator for logging function calls.

    Logs:
    - Function execution start
    - Function arguments (optional)
    - Successful completion
    - Errors
    - Execution time

    Usage:
    ```python
    @log
    async def my_function(arg1, arg2):
        ...
    ```
    """

    def _log_call(
        func_name: str, module: str, args: tuple, kwargs: dict, start_time: datetime
    ) -> None:
        """Log function call start."""
        logger.info(
            f"START {module}.{func_name} "
            f"args={args if len(args) < 3 else '(...)'} "
            f"kwargs={kwargs if len(str(kwargs)) < 100 else '(...)'}"
        )

    def _log_success(func_name: str, module: str, duration: float) -> None:
        """Log successful completion."""
        logger.info(f"SUCCESS {module}.{func_name} " f"duration={duration:.3f}s")

    def _log_error(
        func_name: str, module: str, duration: float, error: Exception
    ) -> None:
        """Log error."""
        logger.error(
            f"ERROR {module}.{func_name} "
            f"duration={duration:.3f}s "
            f"error={type(error).__name__}: {str(error)}",
            exc_info=True,
        )

    @functools.wraps(func)
    async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start_time = datetime.now()
        _log_call(func.__name__, func.__module__, args, kwargs, start_time)

        try:
            result = await cast(Awaitable[R], func(*args, **kwargs))
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            _log_success(func.__name__, func.__module__, duration)
            return result
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            _log_error(func.__name__, func.__module__, duration, e)
            raise

    @functools.wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start_time = datetime.now()
        _log_call(func.__name__, func.__module__, args, kwargs, start_time)

        try:
            result = func(*args, **kwargs)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            _log_success(func.__name__, func.__module__, duration)
            return result
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            _log_error(func.__name__, func.__module__, duration, e)
            raise

    # Return the appropriate wrapper based on the function type
    if inspect.iscoroutinefunction(func):
        return async_wrapper  # type: ignore[return-value]
    return sync_wrapper  # type: ignore[return-value]


def log_database_queries(func: Callable[P, R]) -> Callable[P, R]:
    """Decorator for logging SQL queries"""

    @functools.wraps(func)
    async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        logger.info(f"DATABASE {func.__name__} called")
        return await cast(Awaitable[R], func(*args, **kwargs))

    @functools.wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        logger.info(f"DATABASE {func.__name__} called")
        return func(*args, **kwargs)

    # Return the appropriate wrapper based on the function type
    if inspect.iscoroutinefunction(func):
        return async_wrapper  # type: ignore[return-value]
    return sync_wrapper  # type: ignore[return-value]
