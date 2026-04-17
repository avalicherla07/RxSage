from services.evidence_ranker import (
    get_trust_level,
    compute_relevance_score,
    score_single_evidence,
    detect_conflicts,
    resolve_conflict,
    ScoredEvidence,
    TrustLevel,
)


def test_trust_hierarchy_scoring():
    # FDA drug label (7) > curated DB (6)
    assert get_trust_level("openfda") > get_trust_level("local_db")

    # Curated DB (6) > PubMed case report (2)
    assert get_trust_level("local_db") > get_trust_level("pubmed")

    # PubMed case report (2) > AI summary (1)
    assert get_trust_level("pubmed") > get_trust_level("ai_summary")

    # DailyMed and OpenFDA both map to FDA_DRUG_LABEL (7)
    assert get_trust_level("dailymed") == TrustLevel.FDA_DRUG_LABEL


def test_relevance_scoring():
    # Content mentioning dental terms scores higher than generic content
    dental = compute_relevance_score(
        "dental extraction bleeding risk", 50, [], "ibuprofen"
    )
    generic = compute_relevance_score(
        "general pharmacology overview", 50, [], "ibuprofen"
    )
    assert dental > generic

    # Content containing the candidate drug name scores higher
    with_drug = compute_relevance_score(
        "ibuprofen interaction profile", 50, [], "ibuprofen"
    )
    without_drug = compute_relevance_score(
        "general interaction profile", 50, [], "ibuprofen"
    )
    assert with_drug > without_drug

    # Content matching patient condition scores higher
    with_cond = compute_relevance_score(
        "risk in patients with diabetes", 50, ["diabetes"], "metformin"
    )
    without_cond = compute_relevance_score(
        "risk in healthy volunteers", 50, ["diabetes"], "metformin"
    )
    assert with_cond > without_cond


def test_conflict_detection():
    high_trust = ScoredEvidence(
        source_name="local_db", trust_level=6,
        trust_label="Curated interaction database",
        content="High severity interaction", drug_a="warfarin", drug_b="ibuprofen",
        severity_claim="high", relevance_score=0.7, final_score=0.8,
    )
    low_trust = ScoredEvidence(
        source_name="pubmed", trust_level=2,
        trust_label="PubMed case report",
        content="Minor interaction noted", drug_a="warfarin", drug_b="ibuprofen",
        severity_claim="minor", relevance_score=0.5, final_score=0.4,
    )

    conflicts = detect_conflicts([high_trust, low_trust])

    # Conflict is detected between the two disagreeing sources
    assert len(conflicts) == 1

    # Resolution favours the higher-trust source's claim
    assert resolve_conflict(conflicts[0]) == "high"

    # Conflict is flagged to dentist due to severity gap >= 2
    assert conflicts[0].should_flag_to_dentist is True
