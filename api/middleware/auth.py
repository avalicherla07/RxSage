"""
Auth middleware for Clarvyn API.

Provides the `verify_api_key` FastAPI dependency that validates X-API-Key
headers against Supabase with a 500ms timeout.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging

from fastapi import Header, HTTPException

from db.supabase import SupabaseError, lookup_api_key
from models.response import APIKeyRecord

logger = logging.getLogger(__name__)

_AUTH_TIMEOUT_SECONDS = 5.0


async def verify_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> APIKeyRecord:
    """
    FastAPI dependency injected on all protected routes.

    - Raises HTTP 401 MISSING_API_KEY if the header is absent.
    - Raises HTTP 503 AUTH_TIMEOUT if Supabase lookup exceeds 500ms.
    - Raises HTTP 401 INVALID_API_KEY if the key is not found or revoked.
    - Returns the resolved APIKeyRecord on success.
    """
    if x_api_key is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "Missing API key", "code": "MISSING_API_KEY"},
        )

    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()

    try:
        record = await asyncio.wait_for(
            lookup_api_key(key_hash),
            timeout=_AUTH_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.warning("Supabase key lookup timed out after %sms", _AUTH_TIMEOUT_SECONDS * 1000)
        raise HTTPException(
            status_code=503,
            detail={"error": "Auth service timeout", "code": "AUTH_TIMEOUT"},
        )
    except SupabaseError as exc:
        logger.error("Supabase error during key lookup: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={"error": "Auth service timeout", "code": "AUTH_TIMEOUT"},
        )

    if record is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "Invalid or revoked API key", "code": "INVALID_API_KEY"},
        )

    return record
