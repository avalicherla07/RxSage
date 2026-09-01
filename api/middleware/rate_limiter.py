"""Per-API-key rate limiting for /v1/analyze."""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import HTTPException

logger = logging.getLogger(__name__)

_request_log: dict[str, list[datetime]] = defaultdict(list)
_lock = asyncio.Lock()

RATE_LIMITS = {"per_minute": 10, "per_hour": 100, "per_day": 500}


async def check_rate_limit(api_key_id: str) -> dict[str, int]:
    """Check limits. Raises 429 if exceeded. Returns remaining counts."""
    async with _lock:
        now = datetime.utcnow()
        ts = _request_log[api_key_id]
        ts[:] = [t for t in ts if t > now - timedelta(hours=24)]

        cm = sum(1 for t in ts if t > now - timedelta(minutes=1))
        ch = sum(1 for t in ts if t > now - timedelta(hours=1))
        cd = len(ts)

        for count, limit, code, secs in [
            (cm, "per_minute", "RATE_LIMIT_MINUTE", 60),
            (ch, "per_hour", "RATE_LIMIT_HOUR", 3600),
            (cd, "per_day", "RATE_LIMIT_DAY", 86400),
        ]:
            if count >= RATE_LIMITS[limit]:
                raise HTTPException(status_code=429, detail={
                    "error": "Rate limit exceeded", "code": code,
                    "message": f"Max {RATE_LIMITS[limit]} requests per {limit.split('_')[1]}.",
                    "retry_after_seconds": secs,
                })

        ts.append(now)
        return {
            "remaining_minute": RATE_LIMITS["per_minute"] - cm - 1,
            "remaining_hour": RATE_LIMITS["per_hour"] - ch - 1,
        }
