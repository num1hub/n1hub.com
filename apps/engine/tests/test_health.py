import asyncio

from fastapi.testclient import TestClient

from app.events import event_publisher
from app.main import app


def test_healthz_and_livez_endpoints():
    with TestClient(app) as client:
        healthz = client.get("/healthz")
        livez = client.get("/livez")

    assert healthz.status_code == 200
    assert livez.status_code == 200
    assert healthz.json()["status"] == "ok"
    assert livez.json()["status"] == "live"


def test_readyz_endpoint():
    with TestClient(app) as client:
        response = client.get("/readyz")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_events_stream_sends_job_updates(monkeypatch):
    queue = asyncio.Queue()
    queue.put_nowait(
        {
            "job_id": "test-job-000",
            "code": 200,
            "stage": "done",
            "state": "succeeded",
            "progress": 100,
            "capsule_id": "spec-job",
        }
    )

    async def subscribe_stub(subscriber_id: str):
        return queue

    async def unsubscribe_stub(_: str):
        return None

    monkeypatch.setattr(event_publisher, "subscribe", subscribe_stub)
    monkeypatch.setattr(event_publisher, "unsubscribe", unsubscribe_stub)

    with TestClient(app) as client:
        response = client.get("/events/stream", stream=True)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        lines = []
        for line in response.iter_lines(decode_unicode=True):
            if line:
                lines.append(line)
                break
        response.close()

    assert any("data:" in line for line in lines)
