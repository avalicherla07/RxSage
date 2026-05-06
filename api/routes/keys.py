"""
Key management routes for Clarvyn API.

POST  /v1/keys            — provision a new API key (admin only)
DELETE /v1/keys/{key_id}  — revoke an existing API key (admin only)

Both endpoints require a valid X-Admin-Key header matching settings.admin_key.
"""
from __future__ import annotations

import hashlib
import logging
import secrets

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import Response

from core.config import get_settings
from db.supabase import SupabaseError, revoke_api_key, store_api_key
from models.response import KeyProvisionResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="")


def _check_admin_key(x_admin_key: str | None) -> None:
    """Raise HTTP 401 INVALID_ADMIN_KEY if the admin key is missing or wrong."""
    settings = get_settings()
    if x_admin_key is None or x_admin_key != settings.admin_key:
        raise HTTPException(
            status_code=401,
            detail={"error": "Invalid admin key", "code": "INVALID_ADMIN_KEY"},
        )


@router.post("/v1/keys", response_model=KeyProvisionResponse, status_code=201)
async def provision_key(
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> KeyProvisionResponse:
    """
    Generate a cryptographically random API key, store its SHA-256 hash in
    Supabase, and return the plaintext key once in the response.
    """
    _check_admin_key(x_admin_key)

    plaintext = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(plaintext.encode()).hexdigest()

    try:
        record = await store_api_key(key_hash, label="provisioned")
    except SupabaseError as exc:
        logger.error("Failed to store API key: %s", exc)
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "code": "INTERNAL_ERROR"},
        )

    return KeyProvisionResponse(key_id=record.id, plaintext_key=plaintext)


@router.delete("/v1/keys/{key_id}", status_code=204)
async def revoke_key(
    key_id: str,
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> Response:
    """
    Mark the specified API key as revoked in Supabase.
    Returns 204 on success, 404 if the key_id does not exist.
    """
    _check_admin_key(x_admin_key)

    try:
        found = await revoke_api_key(key_id)
    except SupabaseError as exc:
        logger.error("Failed to revoke API key %s: %s", key_id, exc)
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "code": "INTERNAL_ERROR"},
        )

    if not found:
        raise HTTPException(
            status_code=404,
            detail={"error": "Key not found", "code": "KEY_NOT_FOUND"},
        )

    return Response(status_code=204)
