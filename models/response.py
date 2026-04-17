"""Response models for the Clarvyn API.

The AnalysisResponse always contains three tiers of progressive disclosure:
  Tier 1 (Immediate): headline, proceed, risk_level, flags
  Tier 2 (Standard):  summary, key_interactions, checks, modifications, alternatives,
                       anesthetic_safety, antibiotic_safety, analgesic_safety,
                       sedation_safety, oral_manifestations, procedure_context
  Tier 3 (Deep):      clinical_explanation, risk_factors, sources, monitoring

The API always returns all three tiers. The calling system controls display.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════
# Tier 2 / Tier 3 sub-models
# ═══════════════════════════════════════════════════════════════════════════

class InteractionDetail(BaseModel):
    drug_pair: str          # e.g. "Warfarin + Ibuprofen"
    severity: str           # "high" | "medium" | "low"
    dental_relevance: str   # One-line dental-specific relevance

class PreProcedureCheck(BaseModel):
    check: str              # e.g. "Check INR — must be below 3.5"
    reason: str             # Why this check matters

class ProcedureModification(BaseModel):
    modification: str       # e.g. "Limit epinephrine to 0.04mg max"
    reason: str

class AlternativeMedication(BaseModel):
    name: str               # Drug name
    dosage: str             # Suggested dose
    reason: str             # Why this is safer for this patient

class RiskFactor(BaseModel):
    factor: str             # e.g. "Age 75"
    impact: str             # How it elevates risk

class SourceAttribution(BaseModel):
    name: str
    url: Optional[str] = None
    detail: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════
# Evidence quality models
# ═══════════════════════════════════════════════════════════════════════════

class EvidenceConflictSummary(BaseModel):
    drugs: str
    description: str
    higher_source: str
    lower_source: str
    clinical_significance: str = "medium"

class EvidenceQualitySummary(BaseModel):
    total_sources_consulted: int
    highest_trust_source: str
    sources_used: list[str]
    evidence_conflicts: list[EvidenceConflictSummary] = Field(default_factory=list)
    overall_evidence_quality: str  # "strong" | "moderate" | "limited"
    evidence_quality_reason: str


# ═══════════════════════════════════════════════════════════════════════════
# Dentist workflow sub-models
# ═══════════════════════════════════════════════════════════════════════════

class AnestheticSafety(BaseModel):
    recommended_agent: str
    epinephrine_status: Literal["safe", "limit", "avoid"]
    epinephrine_guidance: Optional[str] = None
    plain_alternative: Optional[str] = None
    interaction_notes: list[str] = Field(default_factory=list)

class AntibioticSafety(BaseModel):
    prophylaxis_indicated: bool = False
    prophylaxis_reason: Optional[str] = None
    prophylaxis_agent: Optional[str] = None
    candidate_antibiotic_status: Optional[str] = None
    safe_alternatives: list[AlternativeMedication] = Field(default_factory=list)
    interaction_notes: list[str] = Field(default_factory=list)

class AnalgesicSafety(BaseModel):
    first_line_recommendation: str
    ibuprofen_status: Literal["safe", "caution", "avoid"]
    acetaminophen_status: Literal["safe", "caution", "avoid"]
    status_notes: list[str] = Field(default_factory=list)
    safe_alternatives: list[AlternativeMedication] = Field(default_factory=list)
    interaction_notes: list[str] = Field(default_factory=list)

class SedationSafety(BaseModel):
    nitrous_oxide_note: str
    oral_sedation_status: Literal["safe", "caution", "contraindicated"]
    oral_sedation_notes: list[str] = Field(default_factory=list)
    recommended_agent: Optional[str] = None
    alternatives: list[str] = Field(default_factory=list)

class OralManifestation(BaseModel):
    medication: str
    effect: str
    dental_relevance: str
    severity: Literal["high", "medium", "low"]

class OralManifestations(BaseModel):
    findings: list[OralManifestation] = Field(default_factory=list)
    no_findings_note: Optional[str] = None

class ProcedureContext(BaseModel):
    procedure_type: Optional[str] = None
    procedure_specific_notes: list[str] = Field(default_factory=list)
    pre_procedure_checks: list[str] = Field(default_factory=list)
    procedure_modifications: list[str] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════
# Main response model — three-tier progressive disclosure
# ═══════════════════════════════════════════════════════════════════════════

class AnalysisResponse(BaseModel):
    """Complete three-tier clinical analysis. Always fully populated."""

    # ── Meta ──
    request_id: str = ""

    # ── Tier 1: Immediate — dentist sees without clicking ──
    headline: str = Field(..., min_length=10,
        description="One actionable sentence. The single most important clinical fact.")
    proceed: Literal["safe", "caution", "modify", "do_not_proceed"] = Field(...,
        description="safe | caution | modify | do_not_proceed")
    risk_level: Literal["high", "medium", "low"] = Field(...,
        description="Amplified risk after all patient layers applied")
    flags: list[dict] = Field(default_factory=list)

    # ── Tier 2: Standard — one tap to expand ──
    summary: str = Field(..., min_length=20,
        description="2-3 sentences. Plain language. What, why, action.")
    key_interactions: list[InteractionDetail] = Field(default_factory=list)
    pre_procedure_checks: list[PreProcedureCheck] = Field(default_factory=list)
    procedure_modifications: list[ProcedureModification] = Field(default_factory=list)
    alternative_medications: list[AlternativeMedication] = Field(default_factory=list)

    # ── Tier 2: Dentist workflow sections ──
    anesthetic_safety: Optional[AnestheticSafety] = None
    antibiotic_safety: Optional[AntibioticSafety] = None
    analgesic_safety: Optional[AnalgesicSafety] = None
    sedation_safety: Optional[SedationSafety] = None
    oral_manifestations: Optional[OralManifestations] = None
    procedure_context: Optional[ProcedureContext] = None

    # ── Tier 3: Deep — full clinical detail ──
    clinical_explanation: str = Field(..., min_length=20,
        description="Full mechanism-based explanation for a clinical professional.")
    patient_risk_factors: list[RiskFactor] = Field(default_factory=list)
    dental_implications: str = ""
    physician_referral: Optional[str] = None
    monitoring_recommendations: list[str] = Field(default_factory=list)
    reasoning_layers_used: list[str] = Field(default_factory=list)
    sources: list[SourceAttribution] = Field(default_factory=list)

    # ── Evidence quality (Tier 3) ──
    evidence_quality: Optional[EvidenceQualitySummary] = None

    # ── Cache and normalisation meta ──
    cache_hit: bool = False
    normalised_drug_names: list[dict] = Field(default_factory=list)
    drugs_not_found: list[str] = Field(default_factory=list)

    # ── Meta ──
    confidence: Literal["high", "medium", "low"] = "medium"
    confidence_reason: Optional[str] = None
    fallback: bool = False
    fallback_reason: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════
# Internal models — unchanged, used between orchestrator and external clients
# ═══════════════════════════════════════════════════════════════════════════

class RxNavInteraction(BaseModel):
    drug1: str
    drug2: str
    description: str
    severity: Optional[str] = None
    source_url: str

class FDAWarning(BaseModel):
    drug_name: str
    warning_text: str
    contraindications: list[str] = Field(default_factory=list)
    source_url: str

class PubMedArticle(BaseModel):
    pmid: str
    title: str
    abstract: Optional[str] = None
    url: str

class ExternalData(BaseModel):
    interactions: list[RxNavInteraction] = Field(default_factory=list)
    warnings: list[FDAWarning] = Field(default_factory=list)
    evidence: list[PubMedArticle] = Field(default_factory=list)

class APIKeyRecord(BaseModel):
    id: str
    key_hash: str
    label: Optional[str] = None
    revoked: bool
    created_at: str

class AuditLogEntry(BaseModel):
    api_key_id: str
    request_hash: str
    risk_level: Optional[str] = None
    latency_ms: int
    fallback: bool
    timestamp: str

class KeyProvisionResponse(BaseModel):
    key_id: str
    plaintext_key: str
