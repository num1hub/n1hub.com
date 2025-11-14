import asyncio

from fastapi.testclient import TestClient

from app.events import event_publisher
from app.main import app
import app.main as main_module


async def _noop_async(*_: object, **__: object) -> None:
    return None


def _patch_startup(monkeypatch):
    monkeypatch.setattr(main_module, "_bootstrap_capsules", _noop_async)
    monkeypatch.setattr(main_module, "create_redis_client", _noop_async)
    monkeypatch.setattr(main_module, "redis_client", None, raising=False)


def test_healthz_and_livez_endpoints(monkeypatch):
    _patch_startup(monkeypatch)
    with TestClient(app) as client:
        healthz = client.get("/healthz")
        livez = client.get("/livez")

    assert healthz.status_code == 200
    assert livez.status_code == 200
    assert healthz.json()["status"] == "ok"
    assert livez.json()["status"] == "live"


def test_readyz_endpoint(monkeypatch):
    _patch_startup(monkeypatch)
    with TestClient(app) as client:
        response = client.get("/readyz")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_events_stream_sends_job_updates(monkeypatch):
    _patch_startup(monkeypatch)

    async def subscribe_stub(subscriber_id: str):
        queue = asyncio.Queue()
        await queue.put(
            {
                "job_id": "test-job-000",
                "code": 200,
                "stage": "done",
                "state": "succeeded",
                "progress": 100,
                "capsule_id": "spec-job",
            }
        )
        return queue

    async def unsubscribe_stub(_: str):
        return None

    monkeypatch.setattr(event_publisher, "subscribe", subscribe_stub)
    monkeypatch.setattr(event_publisher, "unsubscribe", unsubscribe_stub)

    async def _run() -> bytes:
        response = await main_module.events_stream()
        iterator = response.body_iterator
        chunk = await iterator.__anext__()
        return chunk if isinstance(chunk, bytes) else chunk.encode("utf-8")

    chunk = asyncio.run(_run())
    assert b"data:" in chunk
