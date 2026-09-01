"""
Supabase async client for Clarvyn API.

Provides typed async functions for API key management, audit logging,
and analysis caching. All Supabase calls are wrapped in try/except and
re-raised as typed exceptions.
"""
from __future__ import annotations

import logging
from typing import Optional

from supabase import AsyncClient, create_async_client

from core.config import get_settings
from models.response import AnalysisResponse, APIKeyRecord, AuditLogEntry

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Typed exceptions
# ---------------------------------------------------------------------------


class SupabaseError(Exception):
    """Base exception for all Supabase client errors."""


class KeyNotFoundError(SupabaseError):
    """Raised when an API key is not found or already revoked."""


class AnalysisNotFoundError(SupabaseError):
    """Raised when a cached analysis is not found for the given request_id."""


# ---------------------------------------------------------------------------
# Singleton async client (lazy initialisation)
# ---------------------------------------------------------------------------

_client: Optional[AsyncClient] = None


async def _get_client() -> AsyncClient:
    """Return the shared async Supabase client, creating it on first call."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = await create_async_client(
            settings.supabase_url,
            settings.supabase_service_key,
        )
    return _client


# ---------------------------------------------------------------------------
# API key operations
# ---------------------------------------------------------------------------


async def lookup_api_key(key_hash: str) -> APIKeyRecord | None:
    """
    Query api_keys where key_hash matches and revoked is False.

    Returns APIKeyRecord if found, None otherwise.
    Raises SupabaseError on unexpected database errors.
    """
    try:
        client = await _get_client()
        result = (
            await client.table("api_keys")
            .select("*")
            .eq("key_hash", key_hash)
            .eq("revoked", False)
            .execute()
        )
        if not result.data:
            return None
        return APIKeyRecord(**result.data[0])
    except SupabaseError:
        raise
    except Exception as exc:
        raise SupabaseError(f"Failed to look up API key: {exc}") from exc


async def store_api_key(key_hash: str, label: str) -> APIKeyRecord:
    """
    Insert a new API key record into api_keys.

    Returns the created APIKeyRecord.
    Raises SupabaseError on failure.
    """
    try:
        client = await _get_client()
        result = (
            await client.table("api_keys")
            .insert({"key_hash": key_hash, "label": label})
            .execute()
        )
        return APIKeyRecord(**result.data[0])
    except SupabaseError:
        raise
    except Exception as exc:
        raise SupabaseError(f"Failed to store API key: {exc}") from exc


async def revoke_api_key(key_id: str) -> bool:
    """
    Mark an API key as revoked by its UUID.

    Returns True if the key was found and revoked, False if not found.
    Raises SupabaseError on unexpected database errors.
    """
    try:
        client = await _get_client()
        result = (
            await client.table("api_keys")
            .update({"revoked": True})
            .eq("id", key_id)
            .execute()
        )
        return len(result.data) > 0
    except SupabaseError:
        raise
    except Exception as exc:
        raise SupabaseError(f"Failed to revoke API key: {exc}") from exc


# ---------------------------------------------------------------------------
# Audit logging
# ---------------------------------------------------------------------------


async def write_audit_log(entry: AuditLogEntry) -> None:
    """
    Insert an audit log entry into audit_logs.

    Raises SupabaseError on failure.
    """
    try:
        client = await _get_client()
        await client.table("audit_logs").insert(
            {
                "api_key_id": entry.api_key_id,
                "request_hash": entry.request_hash,
                "risk_level": entry.risk_level,
                "latency_ms": entry.latency_ms,
                "fallback": entry.fallback,
                "created_at": entry.timestamp,
            }
        ).execute()
    except SupabaseError:
        raise
    except Exception as exc:
        raise SupabaseError(f"Failed to write audit log: {exc}") from exc


# ---------------------------------------------------------------------------
# Analysis caching
# ---------------------------------------------------------------------------


async def cache_analysis(request_id: str, response: AnalysisResponse) -> None:
    """
    Upsert an AnalysisResponse into cached_analyses keyed by request_id.

    Raises SupabaseError on failure.
    """
    try:
        client = await _get_client()
        await client.table("cached_analyses").upsert(
            {
                "request_id": request_id,
                "response": response.model_dump(),
            },
            on_conflict="request_id",
        ).execute()
    except SupabaseError:
        raise
    except Exception as exc:
        raise SupabaseError(f"Failed to cache analysis: {exc}") from exc


async def get_cached_analysis(request_id: str) -> AnalysisResponse | None:
    """
    Retrieve a cached AnalysisResponse by request_id.

    Returns AnalysisResponse if found, None otherwise.
    Raises SupabaseError on unexpected database errors.
    """
    try:
        client = await _get_client()
        result = (
            await client.table("cached_analyses")
            .select("response")
            .eq("request_id", request_id)
            .execute()
        )
        if not result.data:
            return None
        return AnalysisResponse(**result.data[0]["response"])
    except SupabaseError:
        raise
    except Exception as exc:
        raise SupabaseError(f"Failed to retrieve cached analysis: {exc}") from exc
