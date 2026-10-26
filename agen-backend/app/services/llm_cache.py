import functools
import copy
from typing import Callable

def ai_cache(maxsize: int = 1000):
    """
    A custom caching decorator for LLM agent functions.
    It uses lru_cache under the hood but ensures that the returned value
    is deep-copied. This prevents bugs where mutable dicts returned by the AI
    are modified by downstream business logic, corrupting the cache.
    """
    def decorator(func: Callable) -> Callable:
        # The internal cached function
        @functools.lru_cache(maxsize=maxsize)
        def cached_func(*args, **kwargs):
            return func(*args, **kwargs)
            
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Agent functions typically take simple types (str, int) which are hashable.
            result = cached_func(*args, **kwargs)
            return copy.deepcopy(result)
            
        return wrapper
    return decorator
