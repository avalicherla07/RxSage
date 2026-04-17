"""Orchestrator — coordinates external data gathering and AI reasoning.

Two-layer caching strategy:
  Layer 1 — Drug data cache (in-memory, keyed by sorted drug names):
    Caches OpenFDA warnings, DailyMed labels, PubMed articles, and RxNav
    interactions for a given set of drugs. Drug interaction data doesn't
    change between patients — Warfarin + Ibuprofen warnings are the same
    whether the patient is 25 or 75.

  Layer 2 — Full response cache (Supabase, keyed by full request hash):
    Caches the complete GPT-4o analysis for an exact request. Only hits
    when the same patient with the same drugs asks again.

Flow:
  1. Check full response cache (exact match) → return if hit
  2. Check drug data cache (drug names only) → skip external APIs if hit
  3. If drug data cache miss → run local DB + external APIs
  4. Always run GPT-4o fresh with patient-specific context
  5. Cache both layers
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

from db import supabase as db
from models.request import AnalysisRequest, MedicationInput
from models.response import AnalysisResponse, AuditLogEntry, APIKeyRecord, ExternalData
from services import openfda, pubmed, dailymed, interaction_db
from services import kegg_client, medlineplus
from services import openai_client
from services import evidence_ranker

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory drug data cache — keyed by sorted drug names, with TTL
# ---------------------------------------------------------------------------

_DRUG_CACHE_TTL = 30 * 60  # 30 minutes in seconds
_DRUG_CACHE_MAX = 500


class _CacheEntry:
    __slots__ = ("data", "created_at")

    def __init__(self, data: ExternalData) -> None:
        self.data = data
        self.created_at = time.monotonic()

    def is_expired(self) -> bool:
        return (time.monotonic() - self.created_at) > _DRUG_CACHE_TTL


_drug_data_cache: dict[str, _CacheEntry] = {}


def _drug_cache_key(medications: list[MedicationInput], candidate: MedicationInput) -> str:
    """Deterministic key from sorted drug names only (no patient info)."""
    names = sorted(set(
        m.name.strip().lower() for m in [*medications, candidate]
    ))
    return "|".join(names)


def _get_cached_drug_data(key: str) -> ExternalData | None:
    """Return cached drug data if present and not expired."""
    entry = _drug_data_cache.get(key)
    if entry is None:
        return None
    if entry.is_expired():
        del _drug_data_cache[key]
        return None
    return entry.data


def _cache_drug_data(key: str, data: ExternalData) -> None:
    """Store drug data in the in-memory cache with TTL and size limit."""
    # Evict expired entries first
    expired = [k for k, v in _drug_data_cache.items() if v.is_expired()]
    for k in expired:
        del _drug_data_cache[k]
    # Evict oldest if still full
    if len(_drug_data_cache) >= _DRUG_CACHE_MAX:
        oldest = next(iter(_drug_data_cache))
        del _drug_data_cache[oldest]
    _drug_data_cache[key] = _CacheEntry(data)


# ---------------------------------------------------------------------------
# External data gathering
# ---------------------------------------------------------------------------

async def _gather_external_data(request: AnalysisRequest) -> ExternalData:
    """Gather drug interaction data from all sources.

    Checks the drug data cache first. If the same drug combination was
    already looked up (for any patient), reuses that data instead of
    calling OpenFDA/DailyMed/PubMed again.

    The local interaction DB always runs (instant, no network).
    GPT-4o is NOT called here — that happens in analyze() with patient context.
    """
    all_meds = list(request.current_medications) + [request.candidate_medication]
    conditions = request.patient.conditions
    cache_key = _drug_cache_key(request.current_medications, request.candidate_medication)

    # Check drug data cache
    cached = _get_cached_drug_data(cache_key)
    if cached is not None:
        logger.info("Drug data cache HIT for %s", cache_key)
        return cached

    logger.info("Drug data cache MISS for %s — calling external sources", cache_key)

    async def _safe(coro: Any, name: str) -> list:
        try:
            return await asyncio.wait_for(coro, timeout=5.0)
        except Exception as exc:  # noqa: BLE001
            logger.warning("External source %r failed: %s", name, exc)
            return []

    # 1. Local DB — instant, synchronous, always runs
    local_interactions = interaction_db.get_interactions(
        request.current_medications, request.candidate_medication
    )

    # 2. If local DB found high-severity interactions, skip slow external APIs
    #    for interaction data but still fetch FDA warnings for supporting evidence
    has_high_severity = any(
        i.severity and i.severity.lower() in ("high", "contraindicated")
        for i in local_interactions
    )

    if has_high_severity and len(local_interactions) >= 1:
        logger.info(
            "Local DB found %d high-severity interaction(s) — fast path, "
            "running OpenFDA/DailyMed/PubMed/KEGG/MedlinePlus for supporting data",
            len(local_interactions),
        )
        fda_result, dailymed_result, pubmed_result, kegg_result, mlplus_result = await asyncio.gather(
            _safe(openfda.get_warnings(all_meds), "openfda"),
            _safe(dailymed.get_interactions(all_meds), "dailymed"),
            _safe(pubmed.get_evidence(all_meds, conditions), "pubmed"),
            _safe(kegg_client.get_drug_interactions(all_meds), "kegg"),
            _safe(medlineplus.get_drug_info(all_meds), "medlineplus"),
        )
    else:
        # Full pipeline — all sources concurrent (no RxNav — API deprecated)
        fda_result, dailymed_result, pubmed_result, kegg_result, mlplus_result = await asyncio.gather(
            _safe(openfda.get_warnings(all_meds), "openfda"),
            _safe(dailymed.get_interactions(all_meds), "dailymed"),
            _safe(pubmed.get_evidence(all_meds, conditions), "pubmed"),
            _safe(kegg_client.get_drug_interactions(all_meds), "kegg"),
            _safe(medlineplus.get_drug_info(all_meds), "medlineplus"),
        )

    # Interactions come from local DB only
    all_interactions = list(local_interactions)

    # Merge warnings: OpenFDA + DailyMed + KEGG + MedlinePlus
    all_warnings = (
        (fda_result if isinstance(fda_result, list) else [])
        + (dailymed_result if isinstance(dailymed_result, list) else [])
        + (kegg_result if isinstance(kegg_result, list) else [])
        + (mlplus_result if isinstance(mlplus_result, list) else [])
    )

    result = ExternalData(
        interactions=all_interactions,
        warnings=all_warnings,
        evidence=pubmed_result if isinstance(pubmed_result, list) else [],
    )

    logger.info(
        "Data gathered — interactions: %d (local: %d), warnings: %d, pubmed: %d",
        len(all_interactions), len(local_interactions),
        len(all_warnings), len(result.evidence),
    )

    # Cache the drug data for future requests with different patients
    _cache_drug_data(cache_key, result)

    return result


# ---------------------------------------------------------------------------
# Main analysis pipeline
# ---------------------------------------------------------------------------

async def analyze(
    request: AnalysisRequest,
    key_record: APIKeyRecord,
) -> tuple[AnalysisResponse, str]:
    """Run the full analysis pipeline.

    1. Check full response cache (exact request match) → return if hit
    2. Gather drug data (uses drug data cache if available)
    3. Run GPT-4o with drug data + patient-specific context (always fresh)
    4. Cache the full response
    5. Write audit log

    Patient-specific factors (age, sex, conditions, allergies) are always
    sent to GPT-4o even when drug data is cached. A 75-year-old with heart
    failure gets different recommendations than a 30-year-old, even for the
    same drug combination.
    """
    t_start = time.monotonic()

    # 0. Normalise drug names
    from services.drug_normaliser import normalise_drug_name
    normalised_names: list[dict] = []
    for med in request.current_medications:
        original = med.name
        clean = normalise_drug_name(original)
        if clean != original.lower().strip():
            normalised_names.append({"original": original, "normalised": clean})
            med.name = clean
            logger.info("Drug normalised: %r → %r", original, clean)

    orig_candidate = request.candidate_medication.name
    clean_candidate = normalise_drug_name(orig_candidate)
    if clean_candidate != orig_candidate.lower().strip():
        normalised_names.append({"original": orig_candidate, "normalised": clean_candidate})
        request.candidate_medication.name = clean_candidate
        logger.info("Candidate normalised: %r → %r", orig_candidate, clean_candidate)

    # 1. Deterministic request ID (includes patient info)
    request_id = hashlib.sha256(
        json.dumps(request.model_dump(), sort_keys=True).encode()
    ).hexdigest()

    # 2. Full response cache check (exact match only)
    cached = await db.get_cached_analysis(request_id)
    if cached is not None:
        logger.info("Full response cache HIT for %s", request_id[:12])
        cached.cache_hit = True
        return cached, request_id

    # 3. Gather drug interaction data (may use drug data cache)
    verified_data = await _gather_external_data(request)

    # 3b. Add condition-aware interactions (drug-class + patient-condition)
    all_meds = list(request.current_medications) + [request.candidate_medication]
    condition_interactions = interaction_db.get_condition_interactions(
        all_meds, request.patient.conditions
    )
    if condition_interactions:
        # Merge into verified_data without duplicating
        existing_keys = {
            (i.drug1.lower(), i.description[:50])
            for i in verified_data.interactions
        }
        for ci in condition_interactions:
            key = (ci.drug1.lower(), ci.description[:50])
            if key not in existing_keys:
                existing_keys.add(key)
                verified_data.interactions.append(ci)

    # 3c. Compute risk amplification factors
    amplification_factors = interaction_db.compute_risk_amplification(
        age=request.patient.age,
        conditions=request.patient.conditions,
        medication_count=len(request.current_medications) + 1,
    )

    # 3d. Compute minimum risk level — GPT-4o cannot go below this
    min_risk = interaction_db.compute_minimum_risk_level(
        verified_data.interactions, amplification_factors
    )

    logger.info(
        "Risk amplification: %d factor(s), minimum_risk=%s",
        len(amplification_factors), min_risk,
    )

    # 4. Score and rank all evidence
    scored_evidence: list[evidence_ranker.ScoredEvidence] = []

    # Score interactions from local DB / RxNav
    for ix in verified_data.interactions:
        scored_evidence.append(evidence_ranker.score_single_evidence(
            source_name="local_db",
            source_url=ix.source_url,
            content=ix.description,
            drug_a=ix.drug1, drug_b=ix.drug2,
            severity_claim=ix.severity,
            patient_age=request.patient.age,
            patient_conditions=request.patient.conditions,
            candidate_name=request.candidate_medication.name,
        ))

    # Score FDA / DailyMed / KEGG / MedlinePlus warnings
    for w in verified_data.warnings:
        if w.warning_text.startswith("[DailyMed]"):
            src = "dailymed"
        elif w.warning_text.startswith("[KEGG"):
            src = "kegg"
        elif w.warning_text.startswith("[MedlinePlus]"):
            src = "medlineplus"
        else:
            src = "openfda"
        scored_evidence.append(evidence_ranker.score_single_evidence(
            source_name=src,
            source_url=w.source_url,
            content=w.warning_text,
            drug_a=w.drug_name, drug_b=request.candidate_medication.name,
            severity_claim=None,
            patient_age=request.patient.age,
            patient_conditions=request.patient.conditions,
            candidate_name=request.candidate_medication.name,
        ))

    # Score PubMed articles
    for art in verified_data.evidence:
        scored_evidence.append(evidence_ranker.score_single_evidence(
            source_name="pubmed",
            source_url=art.url,
            content=f"{art.title}. {art.abstract or ''}",
            drug_a=request.current_medications[0].name if request.current_medications else "",
            drug_b=request.candidate_medication.name,
            severity_claim=None,
            patient_age=request.patient.age,
            patient_conditions=request.patient.conditions,
            candidate_name=request.candidate_medication.name,
            publication_year=None,
            study_type=None,
        ))

    # Build ranked package
    evidence_package = evidence_ranker.build_evidence_package(scored_evidence)
    evidence_quality_level, evidence_quality_reason = evidence_ranker.compute_evidence_quality(evidence_package)

    logger.info(
        "Evidence ranked: %d items, %d conflicts (%d flagged), quality=%s",
        evidence_package.total_evidence_items,
        len(evidence_package.conflicts),
        len(evidence_package.flagged_conflicts),
        evidence_quality_level,
    )

    # 5. GPT-4o reasoning — with ranked evidence
    response = await openai_client.reason(
        verified_data, request.patient,
        min_risk_level=min_risk,
        amplification_factors=amplification_factors,
        evidence_package=evidence_package,
    )

    # 5b. Attach evidence quality to response
    from models.response import EvidenceQualitySummary, EvidenceConflictSummary
    conflict_summaries = [
        EvidenceConflictSummary(
            drugs=f"{c.drug_a} + {c.drug_b}",
            description=c.resolution,
            higher_source=c.higher_trust_source,
            lower_source=c.lower_trust_source,
            clinical_significance="high" if c.severity_gap >= 2 else "medium",
        )
        for c in evidence_package.flagged_conflicts
    ]
    response.evidence_quality = EvidenceQualitySummary(
        total_sources_consulted=len(evidence_package.sources_consulted),
        highest_trust_source=evidence_package.highest_trust_source_used,
        sources_used=evidence_package.sources_consulted,
        evidence_conflicts=conflict_summaries,
        overall_evidence_quality=evidence_quality_level,
        evidence_quality_reason=evidence_quality_reason,
    )

    # 5. Attach request_id
    response.request_id = request_id
    response.normalised_drug_names = normalised_names

    # 6. Async side-effects — do not block the response
    elapsed_ms = int((time.monotonic() - t_start) * 1000)

    audit_entry = AuditLogEntry(
        api_key_id=key_record.id,
        request_hash=request_id,
        risk_level=response.risk_level,
        latency_ms=elapsed_ms,
        fallback=response.fallback,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    asyncio.create_task(db.cache_analysis(request_id, response))
    asyncio.create_task(db.write_audit_log(audit_entry))

    return response, request_id
