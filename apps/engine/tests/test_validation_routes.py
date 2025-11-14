"""Tests for validation routes."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from test_validator import create_test_capsule


def test_validate_capsule_endpoint():
    """Test POST /validate/capsule endpoint."""
    capsule = create_test_capsule()
    
    with TestClient(app) as client:
        response = client.post(
            "/validate/capsule",
            json=capsule.model_dump(),
            params={"strict_mode": False}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "ok" in data
    assert "errors" in data
    assert "warnings" in data
    assert "auto_fixes_applied" in data


def test_validate_capsule_with_errors():
    """Test validation endpoint with invalid capsule."""
    capsule = create_test_capsule(
        neuro_concentrate={"summary": " ".join(["word"] * 50)}  # Too short
    )
    
    with TestClient(app) as client:
        response = client.post(
            "/validate/capsule",
            json=capsule.model_dump(),
            params={"strict_mode": False}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert len(data["errors"]) > 0


def test_validate_batch_endpoint():
    """Test POST /validate/batch endpoint."""
    capsules = [
        create_test_capsule(metadata={"capsule_id": f"01JGXM{i:020d}"})
        for i in range(3)
    ]
    
    with TestClient(app) as client:
        response = client.post(
            "/validate/batch",
            json=[c.model_dump() for c in capsules],
            params={"strict_mode": False}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "ok" in data
    assert "total" in data
    assert data["total"] == 3
    assert "results" in data
    assert len(data["results"]) == 3


def test_validate_batch_with_mixed_results():
    """Test batch validation with some valid and invalid capsules."""
    valid_capsule = create_test_capsule(metadata={"capsule_id": "01JGXM0000000000000000VAL"})
    invalid_capsule = create_test_capsule(
        metadata={"capsule_id": "01JGXM0000000000000000INV"},
        neuro_concentrate={"summary": " ".join(["word"] * 50)}  # Too short
    )
    
    with TestClient(app) as client:
        response = client.post(
            "/validate/batch",
            json=[valid_capsule.model_dump(), invalid_capsule.model_dump()],
            params={"strict_mode": False}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] == 1
    assert data["invalid"] == 1
    assert data["total_errors"] > 0
