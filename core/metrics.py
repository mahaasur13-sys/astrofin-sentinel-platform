"""Метрики производительности агентов."""

import time

from tools.metrics_server import AGENT_DURATION


def track_agent_duration(agent_name: str):
    """Декоратор, замеряющий время выполнения агента."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
            finally:
                AGENT_DURATION.labels(agent_name=agent_name).observe(time.time() - start)
            return result

        return wrapper

    return decorator
