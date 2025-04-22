import asyncio
from typing import Callable, Any, List
import random
from .logging import setup_logger

logger = setup_logger(__name__)

class RetryExhausted(Exception):
    """Raised when all retries have been exhausted."""
    pass

async def _retry_async_operation(
    operation: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential: bool = True
) -> Any:
    """
    Retry an async operation with exponential backoff.
    
    Args:
        operation: Async function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential: Whether to use exponential backoff
        
    Returns:
        Result of the operation if successful
        
    Raises:
        RetryExhausted: If all retries are exhausted
        Exception: Any other exception from the operation
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return await operation()
        except Exception as e:
            last_exception = e
            if attempt == max_retries - 1:
                break
                
            # Calculate delay with jitter
            if exponential:
                delay = min(base_delay * (2 ** attempt) + random.random(), max_delay)
            else:
                delay = base_delay + random.random()
                
            logger.warning(
                f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}. "
                f"Retrying in {delay:.2f}s..."
            )
            await asyncio.sleep(delay)
    
    raise RetryExhausted(f"Operation failed after {max_retries} attempts: {str(last_exception)}")

async def run_tasks_concurrently(
    tasks: List[Callable],
    max_concurrent: int,
    return_exceptions: bool = False
) -> List[Any]:
    """
    Run a list of async tasks with a concurrency limit.
    
    Args:
        tasks: List of async coroutines to run
        max_concurrent: Maximum number of concurrent tasks
        return_exceptions: Whether to return exceptions instead of raising
        
    Returns:
        List of results in the same order as tasks
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def _bounded_task(coro):
        async with semaphore:
            return await coro
    
    return await asyncio.gather(
        *[_bounded_task(task) for task in tasks],
        return_exceptions=return_exceptions
    ) 