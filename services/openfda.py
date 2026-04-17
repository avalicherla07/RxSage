"""OpenFDA client — drug labels + adverse events.

Two data sources:
1. Drug labels (/drug/label.json) — warnings, contraindications, drug_interactions sections
2. Adverse events (/drug/event.json) — real-world co-prescription adverse event reports
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx
from pydantic import ValidationError

from models.request import MedicationInput
from models.response import FDAWarning

logger = logging.getLogger(__name__)

_LABEL_URL = "https://api.fda.gov/drug/label.json"
_EVENT_URL = "https://api.fda.gov/drug/event.json"
_SOURCE_URL = "https://open.fda.gov/"
_TIMEOUT = 5.0


async def _safe_call(coro: Any, source_name: str) -> list:
    try:
        return await asyncio.wait_for(coro, timeout=_TIMEOUT)
    except (asyncio.TimeoutError, httpx.HTTPStatusError, ValidationError, Exception) as exc:
        logger.warning("%s failed: %s", source_name, exc)
        return []


# ---------------------------------------------------------------------------
# Drug labels — warnings, contraindications, drug_interactions
# ---------------------------------------------------------------------------

async def _fetch_label_warnings(name: str) -> list[FDAWarning]:
    """Query OpenFDA drug label API for a single medication."""
    search = f'openfda.brand_name:"{name}"+openfda.generic_name:"{name}"'
    async with httpx.AsyncClient() as client:
        resp = await client.get(_LABEL_URL, params={"search": search, "limit": 3})
        resp.raise_for_status()
        data = resp.json()

    results: list[FDAWarning] = []
    for result in data.get("results", []):
        # Collect all relevant text sections
        sections: list[str] = []

        for field in ("warnings", "drug_interactions", "contraindications"):
            val = result.get(field)
            if val and isinstance(val, list) and val[0]:
                sections.append(val[0][:2000])

        contraindications: list[str] = []
        contra_val = result.get("contraindications")
        if contra_val and isinstance(contra_val, list):
            contraindications = [contra_val[0][:1000]]

        warning_text = " | ".join(sections) if sections else ""
        if not warning_text:
            continue

        try:
            results.append(FDAWarning(
                drug_name=name, warning_text=warning_text,
                contraindications=contraindications, source_url=_SOURCE_URL,
            ))
        except ValidationError as exc:
            logger.warning("Skipping invalid FDAWarning for %r: %s", name, exc)

    return results


# ---------------------------------------------------------------------------
# Adverse events — real-world co-prescription reports
# ---------------------------------------------------------------------------

async def _fetch_adverse_events(drug_names: list[str]) -> list[FDAWarning]:
    """Query OpenFDA adverse events for co-reported drugs."""
    if len(drug_names) < 2:
        return []

    # Build query: all drugs must appear in the same report
    drug_clauses = [
        f'patient.drug.openfda.generic_name:"{name}"'
        for name in drug_names[:4]  # limit to avoid overly complex queries
    ]
    search = "+AND+".join(drug_clauses)

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                _EVENT_URL, params={"search": search, "limit": 10}
            )
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPStatusError, httpx.HTTPError):
        return []

    # Aggregate top reactions
    reaction_counts: dict[str, int] = {}
    for event in data.get("results", []):
        for reaction in event.get("patient", {}).get("reaction", []):
            term = reaction.get("reactionmeddrapt", "")
            if term:
                reaction_counts[term] = reaction_counts.get(term, 0) + 1

    if not reaction_counts:
        return []

    top = sorted(reaction_counts.items(), key=lambda x: -x[1])[:10]
    combo = " + ".join(drug_names[:4])
    warning_text = (
        f"Adverse events reported when {combo} are co-prescribed: "
        + ", ".join(f"{term} ({count} reports)" for term, count in top)
    )

    return [FDAWarning(
        drug_name=combo,
        warning_text=warning_text,
        contraindications=[],
        source_url=_SOURCE_URL,
    )]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def get_warnings(medications: list[MedicationInput]) -> list[FDAWarning]:
    """Return FDA warnings from both drug labels and adverse events.

    Queries label API per medication + adverse events for the full drug set.
    """
    warnings: list[FDAWarning] = []

    # Label warnings per medication
    for med in medications:
        result = await _safe_call(
            _fetch_label_warnings(med.name), f"openfda-label({med.name})"
        )
        if isinstance(result, list):
            warnings.extend(result)

    # Adverse events for the full combination
    drug_names = [med.name for med in medications]
    ae_result = await _safe_call(
        _fetch_adverse_events(drug_names), "openfda-events"
    )
    if isinstance(ae_result, list):
        warnings.extend(ae_result)

    logger.info("OpenFDA found %d warning(s)", len(warnings))
    return warnings
