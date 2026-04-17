"""
Tests for Pydantic data models — request validation and response schema.
"""
import pytest
from hypothesis import given, settings as h_settings
from hypothesis import strategies as st
from pydantic import ValidationError

from models.request import AnalysisRequest, MedicationInput, PatientInput, SexEnum
from models.response import (
    AnalysisResponse,
    ConfidenceLevel,
    RiskLevel,
    SourceRef,
)

# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

valid_sex = st.sampled_from([s.value for s in SexEnum])
valid_age = st.integers(min_value=0, max_value=120)
nonempty_text = st.text(min_size=1, max_size=50).filter(str.strip)

medication_strategy = st.builds(
    MedicationInput,
    name=nonempty_text,
    dosage=st.one_of(st.none(), nonempty_text),
    rxcui=st.one_of(st.none(), nonempty_text),
)

patient_strategy = st.builds(
    PatientInput,
    age=valid_age,
    sex=valid_sex,
    conditions=st.lists(nonempty_text, max_size=5),
    allergies=st.lists(nonempty_text, max_size=5),
)

analysis_request_strategy = st.builds(
    AnalysisRequest,
    patient=patient_strategy,
    current_medications=st.lists(medication_strategy, min_size=1, max_size=5),
    candidate_medication=medication_strategy,
)

source_ref_strategy = st.builds(
    SourceRef,
    name=nonempty_text,
    url=st.one_of(st.none(), nonempty_text),
)

analysis_response_strategy = st.builds(
    AnalysisResponse,
    request_id=nonempty_text,
    risk_level=st.sampled_from(list(RiskLevel)),
    summary=nonempty_text,
    clinical_explanation=nonempty_text,
    dental_implications=nonempty_text,
    recommendations=st.lists(nonempty_text, max_size=5),
    alternative_medications=st.lists(nonempty_text, max_size=5),
    confidence=st.sampled_from(list(ConfidenceLevel)),
    sources=st.lists(source_ref_strategy, max_size=5),
    fallback=st.booleans(),
    fallback_reason=st.one_of(st.none(), nonempty_text),
)

# ---------------------------------------------------------------------------
# Property 13: Request validation rejects invalid inputs
# ---------------------------------------------------------------------------

# Feature: clarvyn-python-api, Property 13: Request validation rejects invalid inputs
@given(st.integers().filter(lambda x: x < 0 or x > 120))
@h_settings(max_examples=100)
def test_invalid_age_rejected(age: int):
    """
    Validates: Requirements 8.1, 8.2, 8.3
    Out-of-range age must raise ValidationError.
    """
    with pytest.raises(ValidationError):
        PatientInput(age=age, sex=SexEnum.male)


# Feature: clarvyn-python-api, Property 13: Request validation rejects invalid inputs
@given(st.text().filter(lambda s: s not in ("male", "female", "other")))
@h_settings(max_examples=100)
def test_invalid_sex_rejected(sex: str):
    """
    Validates: Requirements 8.1, 8.2, 8.3
    Invalid sex enum value must raise ValidationError.
    """
    with pytest.raises(ValidationError):
        PatientInput(age=30, sex=sex)


# Feature: clarvyn-python-api, Property 13: Request validation rejects invalid inputs
def test_empty_current_medications_rejected():
    """
    Validates: Requirements 8.1, 8.2, 8.3
    Empty current_medications list must raise ValidationError.
    """
    with pytest.raises(ValidationError):
        AnalysisRequest(
            patient=PatientInput(age=30, sex=SexEnum.male),
            current_medications=[],
            candidate_medication=MedicationInput(name="aspirin"),
        )


# Feature: clarvyn-python-api, Property 13: Request validation rejects invalid inputs
@given(st.just("") | st.just("   "))
@h_settings(max_examples=100)
def test_empty_candidate_medication_name_rejected(name: str):
    """
    Validates: Requirements 8.1, 8.2, 8.3
    Empty or whitespace-only medication name must raise ValidationError.
    """
    with pytest.raises(ValidationError):
        MedicationInput(name=name)


# ---------------------------------------------------------------------------
# Property 14: Optional request fields do not cause validation failure
# ---------------------------------------------------------------------------

# Feature: clarvyn-python-api, Property 14: Optional request fields do not cause validation failure
@given(analysis_request_strategy)
@h_settings(max_examples=100)
def test_optional_fields_accepted(request: AnalysisRequest):
    """
    Validates: Requirements 8.4
    Any valid AnalysisRequest (with or without optional fields) must pass validation.
    """
    # If we got here, Hypothesis built a valid instance — just assert it's the right type
    assert isinstance(request, AnalysisRequest)
    assert isinstance(request.patient, PatientInput)
    assert len(request.current_medications) >= 1
    assert isinstance(request.candidate_medication, MedicationInput)


def test_optional_fields_absent_succeeds():
    """
    Validates: Requirements 8.4
    Omitting conditions, allergies, dosage, and rxcui must not raise ValidationError.
    """
    req = AnalysisRequest(
        patient=PatientInput(age=45, sex=SexEnum.female),
        current_medications=[MedicationInput(name="ibuprofen")],
        candidate_medication=MedicationInput(name="amoxicillin"),
    )
    assert req.patient.conditions == []
    assert req.patient.allergies == []
    assert req.current_medications[0].dosage is None
    assert req.current_medications[0].rxcui is None
    assert req.candidate_medication.dosage is None
    assert req.candidate_medication.rxcui is None


# ---------------------------------------------------------------------------
# Property 15: AnalysisResponse schema completeness
# ---------------------------------------------------------------------------

# Feature: clarvyn-python-api, Property 15: AnalysisResponse schema completeness
@given(st.builds(AnalysisResponse))
@h_settings(max_examples=100)
def test_response_schema_completeness(response: AnalysisResponse):
    """
    **Validates: Requirements 9.2, 11.4**
    Every generated AnalysisResponse must have all 11 required fields.
    """
    required_fields = [
        "request_id", "risk_level", "summary", "clinical_explanation",
        "dental_implications", "recommendations", "alternative_medications",
        "confidence", "sources", "fallback", "fallback_reason",
    ]
    for field in required_fields:
        assert hasattr(response, field), f"Missing required field: {field}"


# ---------------------------------------------------------------------------
# Task 11: End-to-end integration test
# ---------------------------------------------------------------------------

import asyncio
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from main import app
from models.response import (
    APIKeyRecord,
    FDAWarning,
    RxNavInteraction,
)


@pytest.mark.asyncio
async def test_e2e_analyze_returns_valid_response():
    """
    Validates: Requirements 9.1, 9.2, 11.4
    Full end-to-end: POST /v1/analyze returns HTTP 200 with a valid AnalysisResponse.
    """
    valid_key_record = APIKeyRecord(
        id="key-1",
        key_hash="hash",
        revoked=False,
        created_at="2024-01-01T00:00:00",
    )

    mock_interactions = [
        RxNavInteraction(
            drug1="Warfarin",
            drug2="Ibuprofen",
            description="Bleeding risk",
            source_url="https://rxnav.nlm.nih.gov/",
        )
    ]

    mock_warnings = [
        FDAWarning(
            drug_name="Ibuprofen",
            warning_text="May increase bleeding",
            contraindications=[],
            source_url="https://open.fda.gov/",
        )
    ]

    mock_ai_response = AnalysisResponse(
        request_id="test-id",
        risk_level=RiskLevel.medium,
        summary="Potential bleeding risk",
        clinical_explanation="Warfarin and Ibuprofen may interact.",
        dental_implications="Consider alternative analgesic.",
        recommendations=["Monitor INR closely"],
        alternative_medications=["Acetaminophen"],
        confidence=ConfidenceLevel.medium,
        sources=[SourceRef(name="rxnav", url="https://rxnav.nlm.nih.gov/")],
        fallback=False,
        fallback_reason=None,
    )

    request_body = {
        "patient": {"age": 45, "sex": "female", "conditions": [], "allergies": []},
        "current_medications": [{"name": "Warfarin", "rxcui": "11289"}],
        "candidate_medication": {"name": "Ibuprofen"},
    }

    with (
        patch("api.middleware.auth.lookup_api_key", new=AsyncMock(return_value=valid_key_record)),
        patch("services.orchestrator.db.get_cached_analysis", new=AsyncMock(return_value=None)),
        patch("services.orchestrator.db.cache_analysis", new=AsyncMock(return_value=None)),
        patch("services.orchestrator.db.write_audit_log", new=AsyncMock(return_value=None)),
        patch("services.orchestrator.rxnav.get_interactions", new=AsyncMock(return_value=mock_interactions)),
        patch("services.orchestrator.openfda.get_warnings", new=AsyncMock(return_value=mock_warnings)),
        patch("services.orchestrator.pubmed.get_evidence", new=AsyncMock(return_value=[])),
        patch("services.orchestrator.openai_client.reason", new=AsyncMock(return_value=mock_ai_response)),
    ):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/analyze",
                json=request_body,
                headers={"X-API-Key": "test-api-key"},
            )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    data = response.json()
    parsed = AnalysisResponse.model_validate(data)

    assert parsed.request_id, "request_id must be non-empty"
    assert parsed.fallback is False, "fallback must be False"
