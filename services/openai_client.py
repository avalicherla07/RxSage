"""OpenAI client — sends verified interaction data to GPT-4o for clinical reasoning.

Always requests the full three-tier progressive disclosure response.
No conditional logic, no detail_level parameter, no shortcuts.
"""
from __future__ import annotations

import asyncio
import json
import logging

from openai import AsyncOpenAI
from pydantic import ValidationError

from core.config import get_settings
from models.request import PatientInput
from models.response import (
    AnalysisResponse,
    AnestheticSafety,
    AntibioticSafety,
    AnalgesicSafety,
    SedationSafety,
    OralManifestations,
    ProcedureContext,
    ExternalData,
)

logger = logging.getLogger(__name__)

_TIMEOUT = 30.0

_SYSTEM_PROMPT = """\
You are RxSage — a clinical decision support engine for US dental professionals.

You are not a drug database. You are a reasoning engine that takes a full patient picture and produces output in the order a dentist actually needs it at the chair.

Your output must answer seven questions in this exact order:
1. What are the immediate flags for this patient?
2. What is the safest local anesthetic — with or without epinephrine?
3. Is an antibiotic safe, needed, or should an alternative be used?
4. What is the safest pain medication at discharge?
5. Is sedation safe if the patient requests it?
6. What oral effects are the patient's current medications causing?
7. Are there procedure-specific considerations for this visit?

ANESTHETIC RULES:
- Always recommend a specific US dental anesthetic formulation
- Express epinephrine limits as cartridge counts (1.8mL cartridges)
- Non-selective beta-blockers: limit to 2 cartridges of 1:100,000
- Tricyclic antidepressants: limit to 2 cartridges of 1:100,000
- MAO inhibitors: avoid all vasoconstrictors — mepivacaine 3% plain only
- Cardiovascular disease: max 2 cartridges of 1:100,000 (0.04mg total)
- SSRIs: standard doses generally safe

ANTIBIOTIC RULES:
- Always check allergy profile — never suggest a drug the patient is allergic to
- US dental antibiotics: Amoxicillin, Clindamycin, Azithromycin, Metronidazole, Doxycycline
- Flag CYP interactions by enzyme name
- Prophylaxis per AHA 2021 (cardiac) and ADA-AAOS (joints)

ANALGESIC RULES:
- Lead with ibuprofen 400mg + acetaminophen 500mg alternating protocol
- SSRIs + NSAIDs: flag bleeding risk, prefer acetaminophen
- Warfarin + NSAIDs: avoid, use acetaminophen (max 2g/day)
- Opioids: only if non-opioid options contraindicated, note DEA schedule

SEDATION RULES:
- Always surface nitrous oxide first — safest option
- SSRIs + benzodiazepines: prefer triazolam 0.125mg over diazepam
- Opioids + benzodiazepines: flag respiratory depression
- Elderly: lowest effective dose, note fall risk
- Hydroxyzine 25-100mg: always offer as non-controlled alternative

ORAL MANIFESTATIONS — always populate:
- SSRIs: xerostomia, bruxism
- Antipsychotics: severe xerostomia
- Calcium channel blockers: gingival overgrowth
- Bisphosphonates: MRONJ risk
- Phenytoin: gingival overgrowth
- Corticosteroids: impaired healing, candidiasis
- PPIs: reduced calcium absorption
- If no findings: state "No oral side effects detected from current medications"

CRITICAL GROUNDING RULES — APPLY TO EVERY FIELD:
1. NEVER invent drug interactions not present in the VERIFIED EVIDENCE sections below.
2. NEVER claim a drug interaction exists unless it appears in the local DB, OpenFDA,
   DailyMed, KEGG, MedlinePlus, or PubMed evidence provided to you.
3. For anesthetic, antibiotic, analgesic, and sedation recommendations:
   - Base recommendations on the VERIFIED INTERACTIONS and WARNINGS provided
   - The clinical rules below (epinephrine limits, analgesic protocols) are
     ONLY to be applied when the verified evidence supports the underlying interaction
   - If no verified evidence mentions an interaction, do NOT flag it
4. For oral manifestations: only flag effects that are well-established in
   medical literature. Mark each finding with the source of the claim.
5. Every claim in your output must be traceable to either:
   - A specific item in the verified evidence provided, OR
   - A well-established pharmacological fact (e.g., "SSRIs cause xerostomia")
     that you mark as "established pharmacology" in sources
6. If you are uncertain about an interaction, state "insufficient evidence"
   rather than guessing. A false negative is safer than a false positive.
7. The sources field must accurately list ONLY the sources that contributed
   to your reasoning. Do not list sources that returned no relevant data.

TONE: Confident but advisory. Use "consider", "review", "be aware of".
Never absolute commands. Never vague. Always dental-first.

US FORMULARY: Acetaminophen (not paracetamol), Lidocaine (not lignocaine), Epinephrine (not adrenaline).

TIER 1 — IMMEDIATE (dentist sees without clicking):
- headline: ONE actionable sentence. The single most important clinical fact.
- proceed: EXACTLY one of: "safe", "caution", "modify", "do_not_proceed"
- risk_level: "high", "medium", or "low" — reflects amplified risk after patient factors
- flags: list of immediate flags with label and severity

TIER 2 — STANDARD (one tap to expand):
- summary: 2-3 sentences, plain language, no unexplained acronyms
- key_interactions: every interaction found, each with severity and dental relevance
- pre_procedure_checks: specific and measurable
- procedure_modifications: specific and dosage-aware
- alternative_medications: named drug, dose, reason for this patient
- anesthetic_safety: recommended agent, epinephrine status, guidance
- antibiotic_safety: prophylaxis needs, candidate status, alternatives
- analgesic_safety: first-line recommendation, NSAID/acetaminophen status
- sedation_safety: nitrous oxide note, oral sedation status
- oral_manifestations: medication effects on oral health
- procedure_context: procedure-specific notes and checks

TIER 3 — DEEP (full clinical detail):
- clinical_explanation: full mechanism-based explanation
- patient_risk_factors: which of THIS patient's factors elevated the risk
- dental_implications: procedure-aware dental reasoning
- physician_referral: when and why to consult (null if not needed)
- monitoring_recommendations: post-procedure monitoring steps
- reasoning_layers_used: which data sources contributed
- sources: every claim backed by a source name

RULES:
1. Use non-directive language: "consider", "review", "be aware of". Never "must", "should prescribe".
2. For sources.name, use ONLY: "rxnav", "openfda", "dailymed", "pubmed", "local_db", "ai-summary"
3. Always populate EVERY field. Never return empty headline, summary, or clinical_explanation.
4. The headline must be actionable in one sentence — a dentist mid-procedure can act on it.
5. If verified data shows high-severity interactions, risk_level MUST be "high".
6. Always populate anesthetic_safety, analgesic_safety, oral_manifestations even if no concerns.
"""


_RESPONSE_SCHEMA = """\
{
  "headline": "One actionable sentence",
  "proceed": "safe|caution|modify|do_not_proceed",
  "risk_level": "high|medium|low",
  "flags": [{"label": "string", "severity": "high|medium|low|info"}],
  "summary": "2-3 sentences plain language",
  "key_interactions": [{"drug_pair": "Drug A + Drug B", "severity": "high|medium|low", "dental_relevance": "one line"}],
  "pre_procedure_checks": [{"check": "specific check", "reason": "why"}],
  "procedure_modifications": [{"modification": "specific change", "reason": "why"}],
  "alternative_medications": [{"name": "drug", "dosage": "dose", "reason": "why safer"}],
  "anesthetic_safety": {"recommended_agent": "string", "epinephrine_status": "safe|limit|avoid", "epinephrine_guidance": "string or null", "plain_alternative": "string or null", "interaction_notes": ["string"]},
  "antibiotic_safety": {"prophylaxis_indicated": false, "prophylaxis_reason": "string or null", "prophylaxis_agent": "string or null", "candidate_antibiotic_status": "string or null", "safe_alternatives": [{"name": "drug", "dosage": "dose", "reason": "why"}], "interaction_notes": ["string"]},
  "analgesic_safety": {"first_line_recommendation": "string", "ibuprofen_status": "safe|caution|avoid", "acetaminophen_status": "safe|caution|avoid", "status_notes": ["string"], "safe_alternatives": [], "interaction_notes": ["string"]},
  "sedation_safety": {"nitrous_oxide_note": "Nitrous oxide/oxygen — no drug interactions, reversible", "oral_sedation_status": "safe|caution|contraindicated", "oral_sedation_notes": ["string"], "recommended_agent": "string or null", "alternatives": ["string"]},
  "oral_manifestations": {"findings": [{"medication": "string", "effect": "string", "dental_relevance": "string", "severity": "high|medium|low"}], "no_findings_note": "string or null"},
  "procedure_context": {"procedure_type": "string or null", "procedure_specific_notes": ["string"], "pre_procedure_checks": ["string"], "procedure_modifications": ["string"]},
  "clinical_explanation": "Full mechanism-based explanation",
  "patient_risk_factors": [{"factor": "specific factor", "impact": "how it elevates risk"}],
  "dental_implications": "Procedure-aware dental reasoning",
  "physician_referral": "when to consult or null",
  "monitoring_recommendations": ["specific step"],
  "reasoning_layers_used": ["local_db", "openfda", "dailymed", "pubmed"],
  "sources": [{"name": "openfda|dailymed|pubmed|local_db|ai-summary", "url": "or null", "detail": "what it contributed"}],
  "confidence": "high|medium|low",
  "confidence_reason": "why this confidence level",
  "fallback": false,
  "fallback_reason": null
}"""


def _build_user_prompt(verified_data: ExternalData, patient_context: PatientInput) -> str:
    """Build the user prompt from verified external data and patient context."""
    lines: list[str] = []

    lines.append(f"Patient: age={patient_context.age}, sex={patient_context.sex.value}")
    if patient_context.conditions:
        lines.append(f"Conditions: {', '.join(patient_context.conditions)}")
    if patient_context.allergies:
        lines.append(f"Allergies: {', '.join(patient_context.allergies)}")

    lines.append("")
    lines.append("=== VERIFIED DRUG INTERACTIONS (from local DB + RxNav) ===")
    if verified_data.interactions:
        for ix in verified_data.interactions:
            lines.append(f"  [{ix.severity or 'unknown'}] {ix.drug1} + {ix.drug2}: {ix.description[:400]}")
    else:
        lines.append("  No interactions found in verified sources.")

    lines.append("")
    lines.append("=== FDA WARNINGS & DRUG LABELS (from OpenFDA + DailyMed) ===")
    if verified_data.warnings:
        for w in verified_data.warnings:
            source = "DailyMed" if w.warning_text.startswith("[DailyMed]") else "OpenFDA"
            lines.append(f"  [{source}] {w.drug_name}: {w.warning_text[:500]}")
    else:
        lines.append("  No FDA warnings found.")

    lines.append("")
    lines.append("=== PUBMED EVIDENCE ===")
    if verified_data.evidence:
        for art in verified_data.evidence:
            lines.append(f"  [{art.pmid}] {art.title}: {(art.abstract or '')[:200]}")
    else:
        lines.append("  No PubMed articles found.")

    lines.append("")
    lines.append(f"Respond with a JSON object matching this EXACT schema:\n{_RESPONSE_SCHEMA}")
    lines.append("")
    lines.append("IMPORTANT: Populate EVERY field completely. The headline must be one "
                 "actionable sentence. clinical_explanation must be thorough. "
                 "If interactions are high severity, risk_level MUST be 'high'.")

    return "\n".join(lines)


def _build_amplification_context(
    min_risk_level: str,
    amplification_factors: list[tuple[str, str]],
) -> str:
    """Build additional prompt context for risk amplification."""
    if not amplification_factors and min_risk_level == "low":
        return ""

    lines = ["\n=== RISK AMPLIFICATION (deterministic — do not override) ==="]
    lines.append(f"  MINIMUM RISK LEVEL: {min_risk_level}")
    lines.append(f"  You MUST NOT set risk_level below '{min_risk_level}'.")

    if amplification_factors:
        lines.append("  Patient-specific risk amplification factors:")
        for factor_type, reason in amplification_factors:
            lines.append(f"    [{factor_type}] {reason}")
        lines.append("  Include these factors in patient_risk_factors in your response.")

    return "\n".join(lines)


def _validate_grounding(response: AnalysisResponse, verified_data: ExternalData) -> None:
    """Check that GPT-4o's key_interactions are grounded in verified evidence.

    For each claimed interaction, extracts both drug names from the drug_pair
    field and checks whether at least one appears in the verified evidence.
    Ungrounded interactions are tagged directly on the response object and
    confidence is downgraded to "low".
    """
    if not response.key_interactions:
        return

    # Build a set of drug names from verified evidence
    verified_drugs: set[str] = set()
    for ix in verified_data.interactions:
        verified_drugs.add(ix.drug1.lower().strip())
        verified_drugs.add(ix.drug2.lower().strip())
    for w in verified_data.warnings:
        verified_drugs.add(w.drug_name.lower().strip())

    # If no verified data at all, skip the check
    if not verified_drugs:
        return

    ungrounded: list[str] = []
    for ki in response.key_interactions:
        # Split "Drug A + Drug B" into individual names
        pair_drugs = [d.strip().lower() for d in ki.drug_pair.split("+")]
        grounded = any(d in verified_drugs for d in pair_drugs if d)
        if not grounded:
            ungrounded.append(ki.drug_pair)
            ki.dental_relevance += " [UNVERIFIED — not found in validated sources]"

    if ungrounded:
        logger.warning(
            "GPT-4o claimed %d interaction(s) not found in verified evidence: %s",
            len(ungrounded), ungrounded,
        )
        response.confidence = "low"
        response.confidence_reason = (
            f"Grounding check failed: {len(ungrounded)} interaction(s) "
            f"not found in verified sources: {ungrounded}"
        )


def _make_fallback(reason: str) -> AnalysisResponse:
    """Return a structured three-tier fallback response."""
    return AnalysisResponse(
        request_id="",
        headline="AI reasoning unavailable — raw interaction data shown below. Manual review required.",
        proceed="caution",
        risk_level="medium",
        summary="The AI reasoning layer returned an unexpected response. "
                "Verified drug interaction data from NIH and FDA is shown "
                "in key_interactions. Manual clinical review is required.",
        key_interactions=[],
        pre_procedure_checks=[],
        procedure_modifications=[],
        alternative_medications=[],
        clinical_explanation="AI analysis could not be completed. "
                             "See key_interactions for verified source data. "
                             "Manual review by the treating clinician is required.",
        patient_risk_factors=[],
        dental_implications="",
        physician_referral="Manual review required before proceeding.",
        monitoring_recommendations=[],
        reasoning_layers_used=[],
        sources=[],
        confidence="low",
        confidence_reason=f"Fallback: {reason}",
        fallback=True,
        fallback_reason=reason,
        anesthetic_safety=AnestheticSafety(
            recommended_agent="Lidocaine 2% with epinephrine 1:100,000",
            epinephrine_status="safe",
        ),
        antibiotic_safety=AntibioticSafety(),
        analgesic_safety=AnalgesicSafety(
            first_line_recommendation="Ibuprofen 400mg + Acetaminophen 500mg alternating every 3hrs",
            ibuprofen_status="safe",
            acetaminophen_status="safe",
        ),
        sedation_safety=SedationSafety(
            nitrous_oxide_note="Nitrous oxide/oxygen — no drug interactions, reversible, consider as first-line anxiety management.",
            oral_sedation_status="safe",
        ),
        oral_manifestations=OralManifestations(
            no_findings_note="AI reasoning unavailable — oral manifestation assessment requires manual review.",
        ),
        procedure_context=ProcedureContext(),
        flags=[],
    )


async def reason(
    verified_data: ExternalData,
    patient_context: PatientInput,
    min_risk_level: str = "low",
    amplification_factors: list[tuple[str, str]] | None = None,
    evidence_package: object | None = None,
) -> AnalysisResponse:
    """Send verified data to GPT-4o and return a validated three-tier AnalysisResponse.

    If evidence_package is provided, ranked evidence with trust labels is
    included in the prompt so GPT-4o reasons from strongest evidence first.
    """
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    user_prompt = _build_user_prompt(verified_data, patient_context)

    # Add ranked evidence with trust labels if available
    if evidence_package is not None:
        pkg = evidence_package  # RankedEvidencePackage
        ranked = getattr(pkg, "ranked_evidence", [])
        if ranked:
            user_prompt += "\n\n=== RANKED EVIDENCE (highest trust first) ==="
            for i, ev in enumerate(ranked, 1):
                user_prompt += (
                    f"\n  [{i}] {ev.trust_label} (trust: {ev.trust_level}/7, "
                    f"relevance: {ev.relevance_score:.2f})"
                    f"\n      {ev.drug_a} + {ev.drug_b}"
                    f" | severity: {ev.severity_claim or 'not specified'}"
                    f"\n      {ev.content[:300]}"
                )

        flagged = getattr(pkg, "flagged_conflicts", [])
        if flagged:
            user_prompt += "\n\n=== SOURCE CONFLICTS — address in your output ==="
            for c in flagged:
                user_prompt += (
                    f"\n  {c.drug_a} + {c.drug_b}:"
                    f"\n    {c.higher_trust_source} says: {c.higher_trust_claim}"
                    f"\n    {c.lower_trust_source} says: {c.lower_trust_claim}"
                    f"\n    Resolution: {c.resolution}"
                )

    # Add risk amplification context
    amp_context = _build_amplification_context(
        min_risk_level, amplification_factors or []
    )
    if amp_context:
        user_prompt += "\n" + amp_context

    # Add the schema request at the end
    user_prompt += (
        f"\n\nRespond with a JSON object matching this EXACT schema:\n{_RESPONSE_SCHEMA}"
        "\n\nIMPORTANT: Populate EVERY field completely. The headline must be one "
        "actionable sentence. clinical_explanation must be thorough. "
        f"risk_level MUST be at least '{min_risk_level}'."
    )

    async def _call_openai() -> str:
        response = await client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=3000,
        )
        return response.choices[0].message.content or ""

    try:
        raw_json = await asyncio.wait_for(_call_openai(), timeout=_TIMEOUT)
        data = json.loads(raw_json)
        response = AnalysisResponse.model_validate(data)

        # Enforce minimum risk level — deterministic override
        risk_order = {"low": 0, "medium": 1, "high": 2}
        if risk_order.get(response.risk_level, 0) < risk_order.get(min_risk_level, 0):
            logger.info(
                "Upgrading risk_level from %s to %s (minimum floor)",
                response.risk_level, min_risk_level,
            )
            response.risk_level = min_risk_level

        # Post-response grounding check: flag if GPT-4o claims interactions
        # that don't appear in the verified evidence
        _validate_grounding(response, verified_data)

        return response
    except asyncio.TimeoutError:
        logger.warning("OpenAI API timed out after %ss", _TIMEOUT)
        return _make_fallback("AI service timeout")
    except ValidationError as exc:
        logger.warning("OpenAI response failed Pydantic validation: %s", exc)
        return _make_fallback(f"Response validation failed: {exc}")
    except Exception as exc:
        logger.warning("OpenAI call failed: %s", exc)
        return _make_fallback(str(exc))
