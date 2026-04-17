from services.openai_client import _validate_grounding
from models.response import (
    AnalysisResponse,
    InteractionDetail,
    ExternalData,
    RxNavInteraction,
    FDAWarning,
    AnestheticSafety,
    AnalgesicSafety,
    SedationSafety,
    OralManifestations,
    ProcedureContext,
    AntibioticSafety,
)


def _make_response(
    interactions: list[InteractionDetail],
    confidence: str = "high",
) -> AnalysisResponse:
    """Build a minimal valid AnalysisResponse with given interactions."""
    return AnalysisResponse(
        headline="Test headline for grounding check",
        proceed="caution",
        risk_level="medium",
        summary="Test summary for grounding validation purposes.",
        key_interactions=interactions,
        clinical_explanation="Test clinical explanation for grounding.",
        confidence=confidence,
        confidence_reason=None,
        anesthetic_safety=AnestheticSafety(
            recommended_agent="Lidocaine 2%", epinephrine_status="safe",
        ),
        antibiotic_safety=AntibioticSafety(),
        analgesic_safety=AnalgesicSafety(
            first_line_recommendation="Ibuprofen 400mg",
            ibuprofen_status="safe", acetaminophen_status="safe",
        ),
        sedation_safety=SedationSafety(
            nitrous_oxide_note="Safe", oral_sedation_status="safe",
        ),
        oral_manifestations=OralManifestations(),
        procedure_context=ProcedureContext(),
    )


def _make_evidence(drug_pairs: list[tuple[str, str]]) -> ExternalData:
    """Build a minimal ExternalData with RxNavInteraction entries."""
    interactions = [
        RxNavInteraction(
            drug1=a, drug2=b,
            description="Test interaction",
            source_url="https://test.example.com/",
        )
        for a, b in drug_pairs
    ]
    return ExternalData(interactions=interactions)


def test_grounded_interaction_passes_unchanged():
    ki = InteractionDetail(
        drug_pair="Warfarin + Ibuprofen",
        severity="high",
        dental_relevance="Bleeding risk in dental procedures",
    )
    response = _make_response([ki], confidence="high")
    evidence = _make_evidence([("warfarin", "ibuprofen")])

    _validate_grounding(response, evidence)

    assert response.key_interactions[0].dental_relevance == "Bleeding risk in dental procedures"
    assert response.confidence == "high"


def test_ungrounded_interaction_gets_tagged():
    ki = InteractionDetail(
        drug_pair="FakeDrugA + FakeDrugB",
        severity="high",
        dental_relevance="Some claimed relevance",
    )
    response = _make_response([ki], confidence="high")
    evidence = _make_evidence([("warfarin", "ibuprofen")])

    _validate_grounding(response, evidence)

    assert "[UNVERIFIED" in response.key_interactions[0].dental_relevance
    assert response.confidence == "low"


def test_empty_verified_data_skips_check():
    ki = InteractionDetail(
        drug_pair="FakeDrugA + FakeDrugB",
        severity="high",
        dental_relevance="Original relevance text",
    )
    response = _make_response([ki], confidence="high")
    evidence = ExternalData()

    _validate_grounding(response, evidence)

    assert response.key_interactions[0].dental_relevance == "Original relevance text"
    assert response.confidence == "high"
