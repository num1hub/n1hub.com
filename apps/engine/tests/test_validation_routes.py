"""Tests for validation routes."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
import app.main as main_module
from test_validator import create_test_capsule


async def _noop_async(*_: object, **__: object) -> None:
    return None


def _patch_startup(monkeypatch):
    monkeypatch.setattr(main_module, "_bootstrap_capsules", _noop_async)
    monkeypatch.setattr(main_module, "create_redis_client", _noop_async)
    monkeypatch.setattr(main_module, "redis_client", None, raising=False)


def test_validate_capsule_endpoint(monkeypatch):
    """Test POST /validate/capsule endpoint."""
    capsule = create_test_capsule()

    _patch_startup(monkeypatch)
    with TestClient(app) as client:
        response = client.post(
            "/validate/capsule",
            json=capsule.model_dump(mode="json"),
            params={"strict_mode": False}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "ok" in data
    assert "errors" in data
    assert "warnings" in data
    assert "auto_fixes_applied" in data


def test_validate_capsule_with_errors(monkeypatch):
    """Test validation endpoint with invalid capsule."""
    capsule = create_test_capsule(
        neuro_concentrate={"summary": " ".join(["word"] * 50)}  # Too short
    )

    _patch_startup(monkeypatch)
    with TestClient(app) as client:
        response = client.post(
            "/validate/capsule",
            json=capsule.model_dump(mode="json"),
            params={"strict_mode": False}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert len(data["errors"]) > 0


def test_validate_batch_endpoint(monkeypatch):
    """Test POST /validate/batch endpoint."""
    capsules = [
        create_test_capsule(metadata={"capsule_id": f"01JGXM{i:020d}"})
        for i in range(3)
    ]

    _patch_startup(monkeypatch)
    with TestClient(app) as client:
        response = client.post(
            "/validate/batch",
            json=[c.model_dump(mode="json") for c in capsules],
            params={"strict_mode": False}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "ok" in data
    assert "total" in data
    assert data["total"] == 3
    assert "results" in data
    assert len(data["results"]) == 3


def test_validate_batch_with_mixed_results(monkeypatch):
    """Test batch validation with some valid and invalid capsules."""
    valid_capsule = create_test_capsule(metadata={"capsule_id": "01JGXM0000000000000000VALA"})
    invalid_capsule = create_test_capsule(
        metadata={"capsule_id": "01JGXM0000000000000000INVA"},
        neuro_concentrate={"summary": " ".join(["word"] * 50)}  # Too short
    )

    _patch_startup(monkeypatch)
    with TestClient(app) as client:
        response = client.post(
            "/validate/batch",
            json=[
                valid_capsule.model_dump(mode="json"),
                invalid_capsule.model_dump(mode="json"),
            ],
            params={"strict_mode": False}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] == 1
    assert data["invalid"] == 1
    assert data["total_errors"] > 0
