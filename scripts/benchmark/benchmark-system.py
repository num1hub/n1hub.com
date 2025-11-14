#!/usr/bin/env python3
"""Benchmark system performance: concurrent requests, throughput, etc."""

import asyncio
import time
from typing import List, Dict

import httpx


API_URL = "http://127.0.0.1:8000"


async def health_check(client: httpx.AsyncClient) -> Dict:
    """Perform health check."""
    start = time.time()
    response = await client.get(f"{API_URL}/healthz")
    latency = time.time() - start
    response.raise_for_status()
    return {"latency": latency, "status": response.json()["status"]}


async def list_capsules(client: httpx.AsyncClient) -> Dict:
    """List capsules."""
    start = time.time()
    response = await client.get(f"{API_URL}/capsules")
    latency = time.time() - start
    response.raise_for_status()
    capsules = response.json()
    return {"latency": latency, "count": len(capsules)}


async def concurrent_requests(client: httpx.AsyncClient, count: int, endpoint: str) -> List[Dict]:
    """Run concurrent requests."""
    async def single_request():
        if endpoint == "healthz":
            return await health_check(client)
        elif endpoint == "capsules":
            return await list_capsules(client)
        else:
            raise ValueError(f"Unknown endpoint: {endpoint}")
    
    start = time.time()
    results = await asyncio.gather(*[single_request() for _ in range(count)])
    total_time = time.time() - start
    
    return {
        "results": results,
        "total_time": total_time,
        "requests_per_second": count / total_time,
        "avg_latency": sum(r["latency"] for r in results) / len(results),
    }


async def main():
    """Run system benchmarks."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=== System Performance Benchmarks ===\n")
        
        # Health check
        print("1. Health Check")
        try:
            health = await health_check(client)
            print(f"   Latency: {health['latency']:.3f}s")
            print(f"   Status: {health['status']}")
        except Exception as e:
            print(f"   ✗ Failed: {e}")
        print()
        
        # List capsules
        print("2. List Capsules")
        try:
            capsules = await list_capsules(client)
            print(f"   Latency: {capsules['latency']:.3f}s")
            print(f"   Count: {capsules['count']}")
        except Exception as e:
            print(f"   ✗ Failed: {e}")
        print()
        
        # Concurrent health checks
        print("3. Concurrent Health Checks (10 requests)")
        try:
            concurrent = await concurrent_requests(client, 10, "healthz")
            print(f"   Total time: {concurrent['total_time']:.3f}s")
            print(f"   Requests/sec: {concurrent['requests_per_second']:.2f}")
            print(f"   Avg latency: {concurrent['avg_latency']:.3f}s")
        except Exception as e:
            print(f"   ✗ Failed: {e}")
        print()
        
        # Concurrent capsule listing
        print("4. Concurrent Capsule Listing (10 requests)")
        try:
            concurrent = await concurrent_requests(client, 10, "capsules")
            print(f"   Total time: {concurrent['total_time']:.3f}s")
            print(f"   Requests/sec: {concurrent['requests_per_second']:.2f}")
            print(f"   Avg latency: {concurrent['avg_latency']:.3f}s")
        except Exception as e:
            print(f"   ✗ Failed: {e}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
