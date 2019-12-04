from contextlib import contextmanager
from django.conf import settings
from redis import Redis
from redis.lock import Lock
from typing import Generator


@contextmanager
def redis_lock(name: str, **kwargs) -> Generator:
    """
    Acquire a Redis lock. This is a wrapper around redis.lock.Lock(), that also works in tests (there, the lock is
    always granted without any checks).

    Relevant kwargs are:
     - blocking_timeout: how many seconds to try to acquire the lock. Use 0 for a non-blocking lock.
       The default is None, which means we wait forever.
     - timeout: how many seconds to keep the lock for. The default is None, which means it remains locked forever.

    Raises redis.exceptions.LockError if the lock couldn't be acquired or released.
    """
    if settings.DJTRIGGERS_REDIS_URL.startswith('redis'):  # pragma: no cover
        with Lock(redis=Redis.from_url(settings.DJTRIGGERS_REDIS_URL), name=name, **kwargs):
            yield
    else:
        yield
