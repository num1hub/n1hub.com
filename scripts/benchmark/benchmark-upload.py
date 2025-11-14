#!/usr/bin/env python3
"""Benchmark upload performance: measure time to process documents."""

import asyncio
import time
import sys
from pathlib import Path
from typing import List, Dict

import httpx


API_URL = "http://127.0.0.1:8000"


async def upload_document(client: httpx.AsyncClient, title: str, content: str, tags: List[str]) -> Dict:
    """Upload a document and return job info."""
    response = await client.post(
        f"{API_URL}/ingest",
        json={
            "title": title,
            "content": content,
            "tags": tags,
            "include_in_rag": True,
        },
    )
    response.raise_for_status()
    return response.json()


async def wait_for_job(client: httpx.AsyncClient, job_id: str, timeout: int = 60) -> Dict:
    """Wait for job to complete."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        response = await client.get(f"{API_URL}/jobs/{job_id}")
        response.raise_for_status()
        job = response.json()
        if job["state"] in ("succeeded", "failed"):
            return job
        await asyncio.sleep(0.5)
    raise TimeoutError(f"Job {job_id} did not complete within {timeout}s")


async def benchmark_upload(client: httpx.AsyncClient, title: str, content: str, tags: List[str]) -> Dict:
    """Benchmark a single upload."""
    # Upload
    upload_start = time.time()
    job_info = await upload_document(client, title, content, tags)
    upload_time = time.time() - upload_start
    
    # Wait for completion
    process_start = time.time()
    job = await wait_for_job(client, job_info["job_id"])
    process_time = time.time() - process_start
    
    total_time = time.time() - upload_start
    
    return {
        "job_id": job_info["job_id"],
        "capsule_id": job.get("capsule_id"),
        "state": job["state"],
        "upload_time": upload_time,
        "process_time": process_time,
        "total_time": total_time,
        "content_length": len(content),
    }


async def main():
    """Run upload benchmarks."""
    # Sample documents of different sizes
    documents = [
        {
            "title": "Small Document",
            "content": "This is a small test document. " * 10,
            "tags": ["test", "small", "benchmark"],
        },
        {
            "title": "Medium Document",
            "content": "This is a medium test document with more content. " * 100,
            "tags": ["test", "medium", "benchmark"],
        },
        {
            "title": "Large Document",
            "content": "This is a large test document with substantial content. " * 1000,
            "tags": ["test", "large", "benchmark"],
        },
    ]
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        print("=== Upload Performance Benchmarks ===\n")
        
        results = []
        for doc in documents:
            print(f"Testing: {doc['title']} ({len(doc['content'])} chars)")
            try:
                result = await benchmark_upload(client, doc["title"], doc["content"], doc["tags"])
                results.append({**doc, **result})
                print(f"  ✓ Completed in {result['total_time']:.2f}s")
                print(f"    Upload: {result['upload_time']:.3f}s")
                print(f"    Process: {result['process_time']:.2f}s")
                print(f"    State: {result['state']}")
                if result["capsule_id"]:
                    print(f"    Capsule: {result['capsule_id']}")
            except Exception as e:
                print(f"  ✗ Failed: {e}")
            print()
        
        # Summary
        if results:
            print("=== Summary ===")
            avg_total = sum(r["total_time"] for r in results) / len(results)
            avg_process = sum(r["process_time"] for r in results) / len(results)
            print(f"Average total time: {avg_total:.2f}s")
            print(f"Average process time: {avg_process:.2f}s")
            print(f"Success rate: {sum(1 for r in results if r['state'] == 'succeeded')}/{len(results)}")


if __name__ == "__main__":
    asyncio.run(main())
