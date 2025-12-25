from functools import wraps
from typing import Callable


def retry_on_401(func: Callable):
    """Decorator to handle 401 errors"""

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not hasattr(self, "cookies"):
            await self.authenticate()
        response = await func(self, *args, **kwargs)

        if response.status == 401:
            await self.authenticate()
            response = await func(self, *args, **kwargs)
        return response

    return wrapper
