"""DailyMed client — NLM structured drug label data.

DailyMed provides FDA-approved drug labeling in structured XML format.
We extract the "drug interactions" section from each label.

API: https://dailymed.nlm.nih.gov/dailymed/services/
No API key required. Free and public.
"""
from __future__ import annotations

import asyncio
import logging
import xml.etree.ElementTree as ET
from typing import Any

import httpx
from pydantic import ValidationError

from models.request import MedicationInput
from models.response import FDAWarning

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json"
_SPL_URL = "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls"
_SOURCE_URL = "https://dailymed.nlm.nih.gov/"
_TIMEOUT = 5.0

# HL7 SPL namespace
_NS = {"v3": "urn:hl7-org:v3"}


async def _safe_call(coro: Any, source_name: str) -> list:
    try:
        return await asyncio.wait_for(coro, timeout=_TIMEOUT)
    except (asyncio.TimeoutError, httpx.HTTPStatusError, ValidationError, Exception) as exc:
        logger.warning("%s failed: %s", source_name, exc)
        return []


async def _find_spl_id(drug_name: str) -> str | None:
    """Search DailyMed for a drug and return the first SPL set ID."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                _SEARCH_URL, params={"drug_name": drug_name, "pagesize": 1}
            )
            resp.raise_for_status()
            data = resp.json()
        results = data.get("data", [])
        if results:
            return results[0].get("setid")
        return None
    except Exception as exc:
        logger.warning("DailyMed search failed for %r: %s", drug_name, exc)
        return None


async def _fetch_interactions_section(spl_id: str, drug_name: str) -> list[FDAWarning]:
    """Fetch the SPL XML and extract the drug interactions section."""
    url = f"{_SPL_URL}/{spl_id}.xml"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            resp.raise_for_status()
            xml_text = resp.text
    except Exception as exc:
        logger.warning("DailyMed SPL fetch failed for %r: %s", spl_id, exc)
        return []

    return _parse_interactions_from_spl(xml_text, drug_name)


def _parse_interactions_from_spl(xml_text: str, drug_name: str) -> list[FDAWarning]:
    """Parse SPL XML and extract drug interaction text."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        logger.warning("Failed to parse DailyMed XML: %s", exc)
        return []

    results: list[FDAWarning] = []

    # Look for sections with code "34073-7" (Drug Interactions) or "43685-7" (Drug Interactions)
    interaction_codes = {"34073-7", "43685-7"}

    for section in root.iter(f"{{{_NS['v3']}}}section"):
        code_elem = section.find(f"{{{_NS['v3']}}}code")
        if code_elem is None:
            continue
        code = code_elem.get("code", "")
        if code not in interaction_codes:
            continue

        # Extract all text from this section
        texts = []
        for text_elem in section.iter(f"{{{_NS['v3']}}}paragraph"):
            if text_elem.text:
                texts.append(text_elem.text.strip())
            # Also get tail text and nested content
            for child in text_elem:
                if child.text:
                    texts.append(child.text.strip())
                if child.tail:
                    texts.append(child.tail.strip())

        if not texts:
            # Fallback: get all text content
            for text_elem in section.iter(f"{{{_NS['v3']}}}content"):
                if text_elem.text:
                    texts.append(text_elem.text.strip())

        interaction_text = " ".join(t for t in texts if t)[:3000]
        if interaction_text:
            try:
                results.append(FDAWarning(
                    drug_name=drug_name,
                    warning_text=f"[DailyMed] {interaction_text}",
                    contraindications=[],
                    source_url=_SOURCE_URL,
                ))
            except ValidationError as exc:
                logger.warning("Skipping invalid DailyMed warning: %s", exc)

    return results


async def get_interactions(medications: list[MedicationInput]) -> list[FDAWarning]:
    """Return drug interaction text from DailyMed labels for each medication.

    Returns [] on error/timeout. Each result has source_url pointing to DailyMed.
    """
    warnings: list[FDAWarning] = []

    for med in medications:
        spl_id = await _safe_call(
            _find_spl_id(med.name), f"dailymed-search({med.name})"
        )
        if not spl_id or not isinstance(spl_id, str):
            continue

        result = await _safe_call(
            _fetch_interactions_section(spl_id, med.name),
            f"dailymed-spl({med.name})",
        )
        if isinstance(result, list):
            warnings.extend(result)

    logger.info("DailyMed found %d interaction section(s)", len(warnings))
    return warnings
