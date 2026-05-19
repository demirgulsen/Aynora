"""
IP bazlı rate limiting — BaseMiddleware + Upstash Redis
Dakikada 5 istek / IP (Gemini endpoint'leri için)
"""

import time
import os
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

# Gemini'ye giden endpoint prefix'leri
RATE_LIMITED_PATHS = [
    "/outfit/recommend",
    "/outfit/chat-recommend",
]

LIMIT      = 5     # maks istek / pencere
WINDOW     = 60    # saniye


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Basit sliding window rate limiter.
    Upstash Redis varsa Redis kullanır, yoksa in-memory fallback.
    """

    def __init__(self, app):
        super().__init__(app)
        self._memory: dict[str, list[float]] = defaultdict(list)
        self._redis = self._init_redis()

    def _init_redis(self):
        """Upstash Redis bağlantısını dene, başarısız olursa None döndür."""
        try:
            url      = os.getenv("UPSTASH_REDIS_REST_URL")
            token    = os.getenv("UPSTASH_REDIS_REST_TOKEN")
            if not url or not token:
                return None
            from upstash_redis import Redis
            return Redis(url=url, token=token)
        except Exception:
            return None

    def _is_rate_limited_path(self, path: str) -> bool:
        return any(path.startswith(p) for p in RATE_LIMITED_PATHS)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def _check_redis(self, key: str) -> tuple[bool, int]:
        """Redis sliding window. (rate_limited, retry_after)"""
        try:
            now = time.time()
            pipe = self._redis.pipeline()
            pipe.zremrangebyscore(key, 0, now - WINDOW)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, WINDOW)
            results = pipe.execute()
            count = results[1]
            if count >= LIMIT:
                return True, WINDOW
            return False, 0
        except Exception:
            return False, 0   # Redis hatasında geç

    def _check_memory(self, key: str) -> tuple[bool, int]:
        """In-memory sliding window fallback."""
        now = time.time()
        timestamps = self._memory[key]
        # Pencere dışındakileri temizle
        self._memory[key] = [t for t in timestamps if now - t < WINDOW]
        if len(self._memory[key]) >= LIMIT:
            oldest = self._memory[key][0]
            retry_after = int(WINDOW - (now - oldest)) + 1
            return True, retry_after
        self._memory[key].append(now)
        return False, 0

    async def dispatch(self, request: Request, call_next):
        if not self._is_rate_limited_path(request.url.path):
            return await call_next(request)

        ip  = self._get_client_ip(request)
        key = f"rate:{ip}"

        if self._redis:
            limited, retry_after = await self._check_redis(key)
        else:
            limited, retry_after = self._check_memory(key)

        if limited:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Çok fazla istek. Lütfen biraz bekleyin.",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)