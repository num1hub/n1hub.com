from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import settings
from app.middleware import RateLimitMiddleware
from app.main import app
import app.main as main_module


async def _noop_async(*_: object, **__: object) -> None:
    return None


def _patch_startup(monkeypatch):
    monkeypatch.setattr(main_module, "_bootstrap_capsules", _noop_async)
    monkeypatch.setattr(main_module, "create_redis_client", _noop_async)
    monkeypatch.setattr(main_module, "redis_client", None, raising=False)


def _get_rate_limit_middleware() -> RateLimitMiddleware:
    middleware = app.middleware_stack
    while hasattr(middleware, "app"):
        if isinstance(middleware, RateLimitMiddleware):
            return middleware
        middleware = middleware.app  # type: ignore[assignment]
    raise RuntimeError("RateLimitMiddleware not found in middleware stack")


def test_public_capsule_requests_are_rate_limited(monkeypatch):
    _patch_startup(monkeypatch)
    monkeypatch.setattr(settings, "rate_limit_public", 1)

    with TestClient(app, raise_server_exceptions=False) as client:
        first = client.get("/capsules", params={"scope": "public"})
        assert first.status_code == 200

        second = client.get("/capsules", params={"scope": "public"})
        assert second.status_code == 429
        assert second.json()["detail"] == "Rate limit exceeded"

    # Ensure other tests aren't affected by residual counters
    middleware = _get_rate_limit_middleware()
    middleware._in_memory_store.clear()
