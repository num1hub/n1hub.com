import time

from fastapi.testclient import TestClient

from app.main import app


def test_ingest_pipeline_creates_job_and_capsule():
    payload = {
        "title": "Test Capsule",
        "content": "DeepMine should ingest this document into a capsule with valid metadata.",
        "tags": ["spec", "test", "capsule"],
        "include_in_rag": True,
    }

    with TestClient(app) as client:
        response = client.post("/ingest", json=payload)
        assert response.status_code == 200
        job_id = response.json()["job_id"]
        assert job_id

        job_body = None
        for _ in range(20):
            job_response = client.get(f"/jobs/{job_id}")
            assert job_response.status_code == 200
            job_body = job_response.json()
            if job_body["state"] == "succeeded":
                break
            time.sleep(0.1)

        assert job_body is not None
        assert job_body["state"] == "succeeded"
        assert job_body["capsule_id"]

        capsule_response = client.get(f"/capsules/{job_body['capsule_id']}")
        assert capsule_response.status_code == 200
        capsule = capsule_response.json()
        assert capsule["metadata"]["capsule_id"] == job_body["capsule_id"]
        assert capsule["include_in_rag"] is True
