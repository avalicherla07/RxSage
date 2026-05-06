"""Drug knowledge queries — reads drug_classes, class_interactions, and
condition_interactions from Supabase.

All three functions are safe to call from the hot path:
  - get_drug_classes()            never raises; returns empty set on error
  - get_class_interaction_rules() never raises; returns empty list on error
  - get_condition_interaction_rules() never raises; returns empty list on error

get_class_interaction_rules and get_condition_interaction_rules cache their
results in module-level variables with a 5-minute TTL so Supabase is not
queried on every request.
"""
from __future__ import annotations

import logging
import time

from db.supabase import SupabaseError, _get_client

logger = logging.getLogger(__name__)

_CACHE_TTL = 5 * 60  # 5 minutes in seconds

# ---------------------------------------------------------------------------
# Module-level caches for interaction rule tables
# ---------------------------------------------------------------------------

_class_rules_cache: list[tuple[set[str], set[str], str, str]] | None = None
_class_rules_cached_at: float = 0.0

_condition_rules_cache: list[tuple[set[str], set[str], str, str]] | None = None
_condition_rules_cached_at: float = 0.0


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

async def get_drug_classes(drug_name: str) -> set[str]:
    """Return the pharmacological classes for a drug name from Supabase.

    1. Exact match on drug_name (lowercased + stripped), pending_review=false,
       specialty='dental'.
    2. If no exact match, fetch all rows and do a substring match in both
       directions, unioning all matching classes.
    3. Returns an empty set if nothing found or on any error.
    """
    normalised = drug_name.lower().strip()
    try:
        client = await _get_client()

        # Exact match first
        result = (
            await client.table("drug_classes")
            .select("classes")
            .eq("drug_name", normalised)
            .eq("pending_review", False)
            .eq("specialty", "dental")
            .execute()
        )
        if result.data:
            return set(result.data[0]["classes"])

        # Partial / substring match — fetch all rows and check in Python
        all_rows = (
            await client.table("drug_classes")
            .select("drug_name, classes")
            .eq("pending_review", False)
            .eq("specialty", "dental")
            .execute()
        )
        matched: set[str] = set()
        for row in all_rows.data:
            db_name: str = row["drug_name"]
            if db_name in normalised or normalised in db_name:
                matched.update(row["classes"])

        return matched

    except SupabaseError:
        logger.warning("get_drug_classes: Supabase error for %r — returning empty set", drug_name)
        return set()
    except Exception as exc:  # noqa: BLE001
        logger.warning("get_drug_classes: unexpected error for %r: %s — returning empty set", drug_name, exc)
        return set()


async def get_class_interaction_rules() -> list[tuple[set[str], set[str], str, str]]:
    """Return all class interaction rules from Supabase as a list of tuples.

    Each tuple: (classes_a, classes_b, severity, description)

    Results are cached for 5 minutes. Returns an empty list on any error.
    """
    global _class_rules_cache, _class_rules_cached_at

    now = time.time()
    if _class_rules_cache is not None and (now - _class_rules_cached_at) < _CACHE_TTL:
        return _class_rules_cache

    try:
        client = await _get_client()
        result = (
            await client.table("class_interactions")
            .select("classes_a, classes_b, severity, description")
            .eq("pending_review", False)
            .eq("specialty", "dental")
            .execute()
        )
        rules = [
            (set(row["classes_a"]), set(row["classes_b"]), row["severity"], row["description"])
            for row in result.data
        ]
        _class_rules_cache = rules
        _class_rules_cached_at = now
        logger.debug("get_class_interaction_rules: loaded %d rules from Supabase", len(rules))
        return rules

    except SupabaseError:
        logger.warning("get_class_interaction_rules: Supabase error — returning empty list")
        return []
    except Exception as exc:  # noqa: BLE001
        logger.warning("get_class_interaction_rules: unexpected error: %s — returning empty list", exc)
        return []


async def get_condition_interaction_rules() -> list[tuple[set[str], set[str], str, str]]:
    """Return all condition interaction rules from Supabase as a list of tuples.

    Each tuple: (drug_classes, condition_keywords, severity, description)

    Results are cached for 5 minutes. Returns an empty list on any error.
    """
    global _condition_rules_cache, _condition_rules_cached_at

    now = time.time()
    if _condition_rules_cache is not None and (now - _condition_rules_cached_at) < _CACHE_TTL:
        return _condition_rules_cache

    try:
        client = await _get_client()
        result = (
            await client.table("condition_interactions")
            .select("drug_classes, condition_keywords, severity, description")
            .eq("pending_review", False)
            .eq("specialty", "dental")
            .execute()
        )
        rules = [
            (set(row["drug_classes"]), set(row["condition_keywords"]), row["severity"], row["description"])
            for row in result.data
        ]
        _condition_rules_cache = rules
        _condition_rules_cached_at = now
        logger.debug("get_condition_interaction_rules: loaded %d rules from Supabase", len(rules))
        return rules

    except SupabaseError:
        logger.warning("get_condition_interaction_rules: Supabase error — returning empty list")
        return []
    except Exception as exc:  # noqa: BLE001
        logger.warning("get_condition_interaction_rules: unexpected error: %s — returning empty list", exc)
        return []
