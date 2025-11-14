"""Feature flags system for N1Hub v0.1."""

from __future__ import annotations

import os
from typing import Optional

from .config import settings


class FeatureFlags:
    """Feature flags manager with env var and Redis support."""

    def __init__(self) -> None:
        self._flags: dict[str, bool] = {}
        self._load_from_env()

    def _load_from_env(self) -> None:
        """Load feature flags from environment variables."""
        self._flags = {
            "ff.graph.hop2": os.getenv("N1HUB_FF_GRAPH_HOP2", "false").lower() == "true",
            "ff.audio.ingest": os.getenv("N1HUB_FF_AUDIO_INGEST", "false").lower() == "true",
            "ff.public.market": os.getenv("N1HUB_FF_PUBLIC_MARKET", "false").lower() == "true",
            "ff.eval.dashboard": os.getenv("N1HUB_FF_EVAL_DASHBOARD", "true").lower() == "true",
            "ff.link.suggester": os.getenv("N1HUB_FF_LINK_SUGGESTER", "true").lower() == "true",
        }

    async def _load_from_redis(self) -> None:
        """Load feature flags from Redis (if available)."""
        # Note: Currently using environment variables for feature flags.
        # Future enhancement: Implement Redis-based feature flags for dynamic updates without restart.
        # For now, flags are loaded from env vars only
        pass

    def is_enabled(self, flag_name: str) -> bool:
        """Check if a feature flag is enabled."""
        return self._flags.get(flag_name, False)

    def get_all(self) -> dict[str, bool]:
        """Get all feature flags."""
        return self._flags.copy()


# Global feature flags instance
feature_flags = FeatureFlags()
