#!/usr/bin/env python3
"""Benchmark chat query performance: measure latency and quality."""

import asyncio
import time
from typing import List, Dict

import httpx


API_URL = "http://127.0.0.1:8000"


async def run_chat_query(client: httpx.AsyncClient, query: str, scope: List[str]) -> Dict:
    """Run a chat query and return response."""
    start_time = time.time()
    response = await client.post(
        f"{API_URL}/chat",
        json={"query": query, "scope": scope},
    )
    response.raise_for_status()
    latency = time.time() - start_time
    data = response.json()
    return {
        "query": query,
        "scope": scope,
        "latency": latency,
        "answer_length": len(data.get("answer", "")),
        "sources_count": len(data.get("sources", [])),
        "metrics": data.get("metrics", {}),
    }


async def main():
    """Run chat benchmarks."""
    queries = [
        ("What is machine learning?", ["my"]),
        ("Explain neural networks", ["my"]),
        ("What are the best practices?", ["my"]),
        ("Summarize recent content", ["inbox"]),
        ("Tell me about machine learning", ["public"]),
    ]
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("=== Chat Query Performance Benchmarks ===\n")
        
        results = []
        for query, scope in queries:
            print(f"Query: {query}")
            print(f"Scope: {scope}")
            try:
                result = await run_chat_query(client, query, scope)
                results.append(result)
                print(f"  ✓ Latency: {result['latency']:.3f}s")
                print(f"    Answer length: {result['answer_length']} chars")
                print(f"    Sources: {result['sources_count']}")
                if result["metrics"]:
                    print(f"    Metrics: {result['metrics']}")
            except Exception as e:
                print(f"  ✗ Failed: {e}")
            print()
        
        # Summary
        if results:
            print("=== Summary ===")
            avg_latency = sum(r["latency"] for r in results) / len(results)
            avg_sources = sum(r["sources_count"] for r in results) / len(results)
            print(f"Average latency: {avg_latency:.3f}s")
            print(f"Average sources: {avg_sources:.1f}")
            print(f"Success rate: {len(results)}/{len(queries)}")


if __name__ == "__main__":
    asyncio.run(main())
