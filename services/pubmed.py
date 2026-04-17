"""PubMed client — queries PubMed E-utilities for clinical evidence."""
from __future__ import annotations

import asyncio
import logging
import xml.etree.ElementTree as ET
from typing import Any

import httpx
from pydantic import ValidationError

from core.config import get_settings
from models.request import MedicationInput
from models.response import PubMedArticle

logger = logging.getLogger(__name__)

_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
_TIMEOUT = 5.0


async def _safe_call(coro: Any, source_name: str) -> list:
    """Wrap a coroutine with a 5s timeout; return [] on any failure."""
    try:
        return await asyncio.wait_for(coro, timeout=_TIMEOUT)
    except asyncio.TimeoutError as exc:
        logger.warning("%s timed out: %s", source_name, exc)
        return []
    except httpx.HTTPStatusError as exc:
        logger.warning("%s HTTP error: %s", source_name, exc)
        return []
    except ValidationError as exc:
        logger.warning("%s validation error: %s", source_name, exc)
        return []
    except Exception as exc:  # noqa: BLE001
        logger.warning("%s unexpected error: %s", source_name, exc)
        return []


async def _fetch_evidence(query: str) -> list[PubMedArticle]:
    """Run esearch then efetch and return parsed PubMedArticle list."""
    async with httpx.AsyncClient() as client:
        # Step 1: esearch to get PMIDs
        search_resp = await client.get(
            _ESEARCH_URL,
            params={"db": "pubmed", "term": query, "retmax": 5, "retmode": "json"},
        )
        search_resp.raise_for_status()
        search_data = search_resp.json()

        pmids: list[str] = search_data.get("esearchresult", {}).get("idlist", [])
        if not pmids:
            return []

        # Step 2: efetch to get abstracts
        fetch_resp = await client.get(
            _EFETCH_URL,
            params={
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
                "rettype": "abstract",
            },
        )
        fetch_resp.raise_for_status()
        xml_text = fetch_resp.text

    return _parse_pubmed_xml(xml_text)


def _parse_pubmed_xml(xml_text: str) -> list[PubMedArticle]:
    """Parse PubMed efetch XML and return a list of PubMedArticle."""
    articles: list[PubMedArticle] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        logger.warning("Failed to parse PubMed XML: %s", exc)
        return []

    for article_elem in root.findall(".//PubmedArticle"):
        # Extract PMID
        pmid_elem = article_elem.find(".//PMID")
        if pmid_elem is None or not pmid_elem.text:
            continue
        pmid = pmid_elem.text.strip()

        # Extract title
        title_elem = article_elem.find(".//ArticleTitle")
        title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""

        # Extract abstract
        abstract_parts = article_elem.findall(".//AbstractText")
        abstract: str | None = None
        if abstract_parts:
            abstract = " ".join(
                (part.text or "").strip()
                for part in abstract_parts
                if part.text
            ) or None

        try:
            articles.append(
                PubMedArticle(
                    pmid=pmid,
                    title=title,
                    abstract=abstract,
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                )
            )
        except ValidationError as exc:
            logger.warning("Skipping invalid PubMedArticle pmid=%r: %s", pmid, exc)

    return articles


async def get_evidence(
    medications: list[MedicationInput],
    conditions: list[str],
) -> list[PubMedArticle]:
    """Return PubMed articles relevant to drug interactions.

    Searches for pairwise drug interaction evidence. Handles both drug-drug
    pairs and drug-procedure pairs (e.g., bisphosphonate + extraction).
    """
    settings = get_settings()
    if not settings.pubmed_enabled:
        return []

    if len(medications) < 2:
        return []

    # Procedure keywords — these aren't drug names, need different search strategy
    _PROCEDURE_KEYWORDS = {"extraction", "implant", "procedure", "surgery", "dental"}

    candidate = medications[-1]
    current = medications[:-1]
    all_articles: list[PubMedArticle] = []
    seen_pmids: set[str] = set()

    def _is_procedure(name: str) -> bool:
        return any(kw in name.lower() for kw in _PROCEDURE_KEYWORDS)

    for med in current[:3]:
        # Build a smarter query depending on whether we're dealing with a procedure
        if _is_procedure(candidate.name):
            # Drug + procedure: search for the drug + dental procedure context
            query = f'"{med.name}" AND (dental extraction OR dental implant OR MRONJ OR osteonecrosis)'
        elif _is_procedure(med.name):
            query = f'"{candidate.name}" AND (dental extraction OR dental implant OR MRONJ OR osteonecrosis)'
        else:
            # Normal drug-drug pair
            query = f'"{med.name}" AND "{candidate.name}" AND (drug interaction OR dental)'

        result = await _safe_call(
            _fetch_evidence(query), f"pubmed({med.name}+{candidate.name})"
        )
        if isinstance(result, list):
            for article in result:
                if article.pmid not in seen_pmids:
                    seen_pmids.add(article.pmid)
                    all_articles.append(article)

    # If no pairwise results, try a broader search with conditions
    if not all_articles and conditions:
        drug_names = [m.name for m in medications if not _is_procedure(m.name)]
        if drug_names:
            broad_query = f'"{drug_names[0]}" AND ({" OR ".join(conditions[:2])}) AND dental'
            result = await _safe_call(
                _fetch_evidence(broad_query), "pubmed(broad)"
            )
            if isinstance(result, list):
                all_articles.extend(result)

    logger.info("PubMed found %d article(s)", len(all_articles))
    return all_articles
