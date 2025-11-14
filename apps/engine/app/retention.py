"""Artifact retention policy management."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from .config import settings
from .store import BaseCapsuleStore
from .store_pg import PostgresCapsuleStore

logger = logging.getLogger(__name__)


async def purge_expired_artifacts(store: BaseCapsuleStore) -> int:
    """Purge expired artifacts based on retention policy."""
    retention_days = settings.retention_days
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
    
    if isinstance(store, PostgresCapsuleStore):
        return await _purge_postgres_artifacts(store, cutoff_date)
    else:
        return await _purge_memory_artifacts(store, cutoff_date)


async def _purge_postgres_artifacts(store: PostgresCapsuleStore, cutoff_date: datetime) -> int:
    """Purge expired artifacts from Postgres store."""
    try:
        pool = await store._get_pool()
        async with pool.acquire() as conn:
            # Delete expired artifacts
            result = await conn.execute(
                """
                DELETE FROM artifacts
                WHERE expires_at IS NOT NULL
                AND expires_at < $1
                """,
                cutoff_date,
            )
            deleted_count = int(result.split()[-1]) if result else 0
            
            if deleted_count > 0:
                logger.info(f"Purged {deleted_count} expired artifacts (cutoff: {cutoff_date.isoformat()})")
            
            return deleted_count
    except Exception as e:
        logger.error(f"Error purging Postgres artifacts: {e}")
        return 0


async def _purge_memory_artifacts(store: BaseCapsuleStore, cutoff_date: datetime) -> int:
    """Purge expired artifacts from memory store."""
    try:
        deleted_count = 0
        for job_id, artifacts in store._artifacts.items():
            original_count = len(artifacts)
            store._artifacts[job_id] = [
                art for art in artifacts
                if art.get("expires_at") is None
                or datetime.fromisoformat(art["expires_at"].replace("Z", "+00:00")) >= cutoff_date
            ]
            deleted_count += original_count - len(store._artifacts[job_id])
        
        if deleted_count > 0:
            logger.info(f"Purged {deleted_count} expired artifacts from memory store")
        
        return deleted_count
    except Exception as e:
        logger.error(f"Error purging memory artifacts: {e}")
        return 0


async def retention_cleanup_task(store: BaseCapsuleStore, interval_seconds: int = 3600) -> None:
    """Background task to periodically purge expired artifacts."""
    while True:
        try:
            await purge_expired_artifacts(store)
        except Exception as e:
            logger.error(f"Retention cleanup task error: {e}")
        
        await asyncio.sleep(interval_seconds)
