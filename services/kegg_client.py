"""KEGG Drug client — ATC classification and CYP enzyme data.

Uses the KEGG REST API to:
1. Resolve drug names to KEGG drug IDs
2. Retrieve ATC classification codes
3. Extract CYP enzyme interaction data from drug entries
4. Get drug-drug interaction pairs from KEGG MEDICUS

API: https://rest.kegg.jp/
No API key required. Free for academic use.
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

import httpx
from pydantic import ValidationError

from models.request import MedicationInput
from models.response import FDAWarning

logger = logging.getLogger(__name__)

_BASE = "https://rest.kegg.jp"
_TIMEOUT = 5.0
_SOURCE_URL = "https://www.kegg.jp/"


async def _safe_call(coro: Any, name: str) -> Any:
    try:
        return await asyncio.wait_for(coro, timeout=_TIMEOUT)
    except Exception as exc:
        logger.warning("%s failed: %s", name, exc)
        return None


async def find_drug_id(drug_name: str) -> str | None:
    """Resolve a drug name to a KEGG drug ID (e.g., 'D00564')."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{_BASE}/find/drug/{drug_name}")
            resp.raise_for_status()
            lines = resp.text.strip().split("\n")
            if lines and lines[0]:
                # First result: "dr:D00564\tWarfarin sodium..."
                return lines[0].split("\t")[0].replace("dr:", "")
        return None
    except Exception as exc:
        logger.warning("KEGG find_drug failed for %r: %s", drug_name, exc)
        return None


async def get_drug_info(drug_id: str) -> dict:
    """Fetch full KEGG drug entry and extract structured fields."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{_BASE}/get/dr:{drug_id}")
            resp.raise_for_status()
            return _parse_kegg_entry(resp.text)
    except Exception as exc:
        logger.warning("KEGG get_drug failed for %r: %s", drug_id, exc)
        return {}


def _parse_kegg_entry(text: str) -> dict:
    """Parse a KEGG flat-file drug entry into a dict."""
    info: dict[str, Any] = {}
    current_field = ""
    current_value: list[str] = []

    for line in text.split("\n"):
        if line.startswith("///"):
            break
        if line and not line[0].isspace():
            # Save previous field
            if current_field:
                info[current_field] = "\n".join(current_value).strip()
            parts = line.split(None, 1)
            current_field = parts[0] if parts else ""
            current_value = [parts[1]] if len(parts) > 1 else []
        else:
            current_value.append(line.strip())

    if current_field:
        info[current_field] = "\n".join(current_value).strip()

    return info


def extract_atc_codes(drug_info: dict) -> list[str]:
    """Extract ATC classification codes from KEGG drug info."""
    # ATC codes appear in the CLASS field
    class_text = drug_info.get("CLASS", "")
    atc_pattern = re.compile(r"[A-Z]\d{2}[A-Z]{2}\d{2}")
    return atc_pattern.findall(class_text)


def extract_cyp_data(drug_info: dict) -> list[str]:
    """Extract CYP enzyme interaction data from KEGG drug info."""
    # CYP data appears in METABOLISM and INTERACTION fields
    cyp_enzymes: list[str] = []
    for field in ("METABOLISM", "INTERACTION", "REMARK"):
        text = drug_info.get(field, "")
        cyp_pattern = re.compile(r"CYP\d[A-Z]\d+", re.IGNORECASE)
        cyp_enzymes.extend(cyp_pattern.findall(text))
    return list(set(cyp_enzymes))


def extract_interaction_text(drug_info: dict) -> str:
    """Extract the INTERACTION field text from KEGG drug info."""
    return drug_info.get("INTERACTION", "")


async def get_drug_interactions(
    medications: list[MedicationInput],
) -> list[FDAWarning]:
    """Query KEGG for drug info and extract interaction/CYP data.

    Returns FDAWarning objects (reusing the model) with KEGG-sourced data.
    """
    results: list[FDAWarning] = []

    for med in medications[:4]:  # limit to avoid rate limiting
        drug_id = await _safe_call(find_drug_id(med.name), f"kegg-find({med.name})")
        if not drug_id:
            continue

        info = await _safe_call(get_drug_info(drug_id), f"kegg-get({med.name})")
        if not info:
            continue

        # Extract interaction text
        interaction_text = extract_interaction_text(info)
        cyp_data = extract_cyp_data(info)
        atc_codes = extract_atc_codes(info)

        parts: list[str] = []
        if interaction_text:
            parts.append(f"[KEGG Interactions] {interaction_text[:500]}")
        if cyp_data:
            parts.append(f"[CYP enzymes] {', '.join(cyp_data)}")
        if atc_codes:
            parts.append(f"[ATC] {', '.join(atc_codes)}")

        if parts:
            try:
                results.append(FDAWarning(
                    drug_name=med.name,
                    warning_text=" | ".join(parts),
                    contraindications=[],
                    source_url=_SOURCE_URL,
                ))
            except ValidationError as exc:
                logger.warning("Skipping invalid KEGG warning for %r: %s", med.name, exc)

    logger.info("KEGG found %d drug info entries", len(results))
    return results
