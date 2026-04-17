"""Evidence ranking and conflict resolution system.

Scores every piece of evidence before it reaches GPT-4o, detects conflicts
between sources, resolves them using a trust hierarchy, and packages
everything in ranked order for the AI prompt.

Trust hierarchy (highest to lowest):
  7 — FDA official drug label (regulatory, manufacturer-submitted)
  6 — RxNav / local interaction database (curated, authoritative)
  5 — PubMed systematic review / meta-analysis
  4 — PubMed RCT
  3 — PubMed observational / cohort study
  2 — PubMed case report
  1 — AI-generated summary
"""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from enum import IntEnum
from typing import Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Trust levels
# ═══════════════════════════════════════════════════════════════════════════

class TrustLevel(IntEnum):
    AI_SUMMARY = 1
    PUBMED_CASE_REPORT = 2
    PUBMED_OBSERVATIONAL = 3
    PUBMED_RCT = 4
    PUBMED_SYSTEMATIC_REVIEW = 5
    RXNAV_DATABASE = 6
    FDA_DRUG_LABEL = 7

TRUST_LABELS: dict[TrustLevel, str] = {
    TrustLevel.AI_SUMMARY: "AI-generated summary",
    TrustLevel.PUBMED_CASE_REPORT: "PubMed case report",
    TrustLevel.PUBMED_OBSERVATIONAL: "PubMed observational study",
    TrustLevel.PUBMED_RCT: "PubMed randomised controlled trial",
    TrustLevel.PUBMED_SYSTEMATIC_REVIEW: "PubMed systematic review",
    TrustLevel.RXNAV_DATABASE: "Curated interaction database",
    TrustLevel.FDA_DRUG_LABEL: "FDA official drug label",
}


# ═══════════════════════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════════════════════

class ScoredEvidence(BaseModel):
    source_name: str
    source_url: Optional[str] = None
    trust_level: int  # TrustLevel value
    trust_label: str
    content: str
    drug_a: str
    drug_b: str
    severity_claim: Optional[str] = None
    publication_year: Optional[int] = None
    study_type: Optional[str] = None
    relevance_score: float
    final_score: float


class EvidenceConflict(BaseModel):
    drug_a: str
    drug_b: str
    conflict_type: str
    higher_trust_claim: str
    lower_trust_claim: str
    higher_trust_source: str
    lower_trust_source: str
    severity_gap: int
    should_flag_to_dentist: bool
    resolution: str


class RankedEvidencePackage(BaseModel):
    ranked_evidence: list[ScoredEvidence]
    conflicts: list[EvidenceConflict]
    flagged_conflicts: list[EvidenceConflict]
    total_evidence_items: int
    sources_consulted: list[str]
    highest_trust_source_used: str


SEVERITY_ORDER = {"minor": 1, "moderate": 2, "major": 3, "high": 3, "contraindicated": 4}


# ═══════════════════════════════════════════════════════════════════════════
# Scoring functions
# ═══════════════════════════════════════════════════════════════════════════

def get_trust_level(source: str, metadata: dict | None = None) -> TrustLevel:
    meta = metadata or {}
    if source in ("openfda", "dailymed"):
        return TrustLevel.FDA_DRUG_LABEL
    if source in ("rxnav", "local_db"):
        return TrustLevel.RXNAV_DATABASE
    if source == "kegg":
        return TrustLevel.RXNAV_DATABASE  # curated database, same tier
    if source == "medlineplus":
        return TrustLevel.FDA_DRUG_LABEL  # NLM-curated, FDA-sourced content
    if source == "pubmed":
        study_type = str(meta.get("study_type", "")).lower()
        if "systematic review" in study_type or "meta-analysis" in study_type:
            return TrustLevel.PUBMED_SYSTEMATIC_REVIEW
        if "randomized" in study_type or "randomised" in study_type or "rct" in study_type:
            return TrustLevel.PUBMED_RCT
        if "observational" in study_type or "cohort" in study_type:
            return TrustLevel.PUBMED_OBSERVATIONAL
        return TrustLevel.PUBMED_CASE_REPORT
    if source == "ai_summary":
        return TrustLevel.AI_SUMMARY
    return TrustLevel.PUBMED_CASE_REPORT


def get_recency_factor(publication_year: int | None) -> float:
    if publication_year is None:
        return 0.8
    age = datetime.now().year - publication_year
    if age <= 5:
        return 1.0
    if age <= 10:
        return 0.9
    if age <= 15:
        return 0.8
    if age <= 25:
        return 0.7
    return 0.6


def compute_relevance_score(
    content: str,
    patient_age: int,
    patient_conditions: list[str],
    candidate_name: str,
) -> float:
    score = 0.5
    lower = content.lower()

    # Dental specificity
    dental_terms = ["dental", "dentist", "oral", "perioral", "endodontic",
                    "periodontal", "maxillofacial", "jaw", "tooth"]
    if any(t in lower for t in dental_terms):
        score += 0.15

    # Procedure relevance
    procedure_terms = ["extraction", "implant", "sedation", "bleeding",
                       "osteonecrosis", "MRONJ"]
    if any(t.lower() in lower for t in procedure_terms):
        score += 0.1

    # Age group
    if patient_age >= 65 and any(t in lower for t in ["elderly", "older adult", "geriatric"]):
        score += 0.1

    # Specific drug name match
    if candidate_name.lower() in lower:
        score += 0.1

    # Patient condition match
    for cond in patient_conditions:
        if cond.lower() in lower:
            score += 0.05

    return min(score, 1.0)


def score_single_evidence(
    source_name: str,
    source_url: str | None,
    content: str,
    drug_a: str,
    drug_b: str,
    severity_claim: str | None,
    patient_age: int,
    patient_conditions: list[str],
    candidate_name: str,
    publication_year: int | None = None,
    study_type: str | None = None,
    metadata: dict | None = None,
) -> ScoredEvidence:
    trust = get_trust_level(source_name, metadata)
    recency = get_recency_factor(publication_year)
    relevance = compute_relevance_score(content, patient_age, patient_conditions, candidate_name)

    trust_norm = trust.value / 7.0
    final_score = (trust_norm * 0.6) + (relevance * 0.3) + (recency * 0.1)

    return ScoredEvidence(
        source_name=source_name,
        source_url=source_url,
        trust_level=trust.value,
        trust_label=TRUST_LABELS[trust],
        content=content[:500],
        drug_a=drug_a,
        drug_b=drug_b,
        severity_claim=severity_claim,
        publication_year=publication_year,
        study_type=study_type,
        relevance_score=round(relevance, 3),
        final_score=round(final_score, 3),
    )


# ═══════════════════════════════════════════════════════════════════════════
# Conflict detection and resolution
# ═══════════════════════════════════════════════════════════════════════════

def detect_conflicts(scored: list[ScoredEvidence]) -> list[EvidenceConflict]:
    by_pair: dict[tuple[str, str], list[ScoredEvidence]] = defaultdict(list)
    for ev in scored:
        if ev.severity_claim:
            key = tuple(sorted([ev.drug_a.lower(), ev.drug_b.lower()]))
            by_pair[key].append(ev)

    conflicts: list[EvidenceConflict] = []
    for pair, evs in by_pair.items():
        if len(evs) < 2:
            continue
        evs.sort(key=lambda e: e.trust_level, reverse=True)
        highest = evs[0]
        for other in evs[1:]:
            if highest.severity_claim != other.severity_claim:
                gap = abs(
                    SEVERITY_ORDER.get(highest.severity_claim or "", 0)
                    - SEVERITY_ORDER.get(other.severity_claim or "", 0)
                )
                conflicts.append(EvidenceConflict(
                    drug_a=pair[0],
                    drug_b=pair[1],
                    conflict_type="severity_disagreement",
                    higher_trust_claim=highest.severity_claim or "unknown",
                    lower_trust_claim=other.severity_claim or "unknown",
                    higher_trust_source=highest.trust_label,
                    lower_trust_source=other.trust_label,
                    severity_gap=gap,
                    should_flag_to_dentist=(
                        gap >= 2
                        or "contraindicated" in [highest.severity_claim, other.severity_claim]
                    ),
                    resolution=(
                        f"Defaulting to {highest.trust_label} "
                        f"({highest.severity_claim}). "
                        f"{other.trust_label} disagrees ({other.severity_claim})."
                    ),
                ))
    return conflicts


def resolve_conflict(conflict: EvidenceConflict) -> str:
    if "contraindicated" in [conflict.higher_trust_claim, conflict.lower_trust_claim]:
        return "contraindicated"
    if conflict.severity_gap >= 2:
        return max(
            conflict.higher_trust_claim,
            conflict.lower_trust_claim,
            key=lambda s: SEVERITY_ORDER.get(s, 0),
        )
    return conflict.higher_trust_claim


# ═══════════════════════════════════════════════════════════════════════════
# Balanced selection + packaging
# ═══════════════════════════════════════════════════════════════════════════

def select_balanced_top(scored: list[ScoredEvidence], max_items: int = 10) -> list[ScoredEvidence]:
    selected: list[ScoredEvidence] = []
    sources_seen: set[str] = set()
    for ev in scored:
        if ev.source_name not in sources_seen:
            selected.append(ev)
            sources_seen.add(ev.source_name)
    for ev in scored:
        if len(selected) >= max_items:
            break
        if ev not in selected:
            selected.append(ev)
    return sorted(selected, key=lambda e: e.final_score, reverse=True)


def build_evidence_package(
    scored: list[ScoredEvidence],
) -> RankedEvidencePackage:
    scored_sorted = sorted(scored, key=lambda e: e.final_score, reverse=True)
    conflicts = detect_conflicts(scored_sorted)
    flagged = [c for c in conflicts if c.should_flag_to_dentist]
    top = select_balanced_top(scored_sorted)

    return RankedEvidencePackage(
        ranked_evidence=top,
        conflicts=conflicts,
        flagged_conflicts=flagged,
        total_evidence_items=len(scored),
        sources_consulted=list({ev.source_name for ev in scored}),
        highest_trust_source_used=scored_sorted[0].trust_label if scored_sorted else "none",
    )


def compute_evidence_quality(package: RankedEvidencePackage) -> tuple[str, str]:
    """Return (quality_level, reason) based on sources used."""
    sources = set(package.sources_consulted)
    has_fda = bool(sources & {"openfda", "dailymed", "medlineplus"})
    has_db = bool(sources & {"local_db", "rxnav", "kegg"})
    has_pubmed = "pubmed" in sources

    if has_fda and has_db:
        return "strong", "Based on FDA drug labels and curated interaction database"
    if has_fda or has_db:
        qual = "FDA drug labels" if has_fda else "curated interaction database"
        extra = " with PubMed evidence" if has_pubmed else ""
        return "strong", f"Based on {qual}{extra}"
    if has_pubmed:
        return "moderate", "Based on PubMed literature — no FDA label data available"
    return "limited", "Limited evidence sources available — manual review recommended"
