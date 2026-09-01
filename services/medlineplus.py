"""MedlinePlus drug information client.

Fetches structured drug interaction data from NLM's MedlinePlus drug pages.
Uses the MedlinePlus Connect API to find drug pages, then extracts the
"Before using" and "Interactions" sections.

API: https://medlineplus.gov/connect/service.html
No API key required. Free and public.
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

_CONNECT_URL = "https://connect.medlineplus.gov/service"
_DRUG_INFO_BASE = "https://medlineplus.gov/druginfo/meds"
_SOURCE_URL = "https://medlineplus.gov/"
_TIMEOUT = 5.0


async def _safe_call(coro: Any, name: str) -> Any:
    try:
        return await asyncio.wait_for(coro, timeout=_TIMEOUT)
    except Exception as exc:
        logger.warning("%s failed: %s", name, exc)
        return None


async def _fetch_drug_page_url(drug_name: str) -> str | None:
    """Use MedlinePlus Connect to find the drug info page URL."""
    try:
        async with httpx.AsyncClient() as client:
            params = {
                "mainSearchCriteria.v.dn": drug_name,
                "mainSearchCriteria.v.cs": "2.16.840.1.113883.6.88",
                "informationRecipient.languageCode.c": "en",
                "knowledgeResponseType": "application/json",
            }
            resp = await client.get(_CONNECT_URL, params=params)
            resp.raise_for_status()

            # Try to parse JSON response
            try:
                data = resp.json()
                entries = data.get("feed", {}).get("entry", [])
                if entries:
                    for entry in entries:
                        links = entry.get("link", [])
                        for link in links:
                            href = link.get("href", "")
                            if "druginfo/meds" in href:
                                return href
            except Exception:
                pass

            # Fallback: parse XML/Atom response
            text = resp.text
            # Look for druginfo URL in the response
            match = re.search(r'href="(https://medlineplus\.gov/druginfo/meds/[^"]+)"', text)
            if match:
                return match.group(1)

        return None
    except Exception as exc:
        logger.warning("MedlinePlus Connect failed for %r: %s", drug_name, exc)
        return None


async def _fetch_drug_page_content(url: str) -> str:
    """Fetch the HTML content of a MedlinePlus drug info page."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, follow_redirects=True)
            resp.raise_for_status()
            return resp.text
    except Exception as exc:
        logger.warning("MedlinePlus page fetch failed for %s: %s", url, exc)
        return ""


def _extract_interaction_sections(html: str) -> str:
    """Extract drug interaction text from MedlinePlus HTML page.

    Looks for sections about drug interactions, "before using", and warnings.
    """
    sections: list[str] = []

    # Pattern 1: "Other medications may interact" sections
    # These are in <div> blocks with specific IDs or headings
    patterns = [
        r'(?:Other medications|drug interactions|interact with)[^<]*(?:<[^>]+>)*([^<]{50,500})',
        r'(?:tell your doctor|tell your dentist)[^<]*(?:<[^>]+>)*([^<]{50,500})',
        r'(?:should not take|do not take|avoid)[^<]*(?:<[^>]+>)*([^<]{50,500})',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        for match in matches[:2]:  # limit per pattern
            clean = re.sub(r'<[^>]+>', ' ', match).strip()
            clean = re.sub(r'\s+', ' ', clean)
            if len(clean) > 30:
                sections.append(clean)

    # Also try to find the "What special precautions" section
    precaution_match = re.search(
        r'precautions should I follow.*?</h\d>(.*?)(?:<h\d|$)',
        html, re.IGNORECASE | re.DOTALL
    )
    if precaution_match:
        text = re.sub(r'<[^>]+>', ' ', precaution_match.group(1))
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) > 50:
            sections.append(text[:800])

    return " | ".join(sections) if sections else ""


async def get_drug_info(
    medications: list[MedicationInput],
) -> list[FDAWarning]:
    """Fetch MedlinePlus drug interaction data for each medication.

    Returns FDAWarning objects with MedlinePlus-sourced interaction text.
    """
    results: list[FDAWarning] = []

    for med in medications[:3]:  # limit to avoid slow responses
        url = await _safe_call(
            _fetch_drug_page_url(med.name), f"medlineplus-connect({med.name})"
        )
        if not url:
            continue

        html = await _safe_call(
            _fetch_drug_page_content(url), f"medlineplus-page({med.name})"
        )
        if not html:
            continue

        interaction_text = _extract_interaction_sections(html)
        if not interaction_text:
            continue

        try:
            results.append(FDAWarning(
                drug_name=med.name,
                warning_text=f"[MedlinePlus] {interaction_text[:1000]}",
                contraindications=[],
                source_url=url,
            ))
        except ValidationError as exc:
            logger.warning("Skipping invalid MedlinePlus warning for %r: %s", med.name, exc)

    logger.info("MedlinePlus found %d drug info entries", len(results))
    return results
