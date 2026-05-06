from models.request import MedicationInput
from services.interaction_db import get_interactions, get_condition_interactions


def _med(name: str) -> MedicationInput:
    return MedicationInput(name=name)


async def test_class_pair_interactions():
    # Warfarin (anticoagulant) + Ibuprofen (nsaid) → high
    results = await get_interactions([_med("warfarin")], _med("ibuprofen"))
    assert any(r.severity == "high" for r in results)

    # Codeine (opioid) + Diazepam (benzodiazepine) → high
    results = await get_interactions([_med("diazepam")], _med("codeine"))
    assert any(r.severity == "high" for r in results)

    # Clarithromycin (cyp3a4_inhibitor) + Simvastatin (cyp3a4_substrate) → high
    results = await get_interactions([_med("simvastatin")], _med("clarithromycin"))
    assert any(r.severity == "high" for r in results)

    # Lidocaine with epinephrine (sympathomimetic) + Carvedilol (nonselective_beta_blocker) → high
    results = await get_interactions([_med("carvedilol")], _med("lidocaine with epinephrine"))
    assert any(r.severity == "high" for r in results)


async def test_drug_condition_rules():
    # NSAID + renal impairment → high
    results = await get_condition_interactions([_med("ibuprofen")], ["renal impairment"])
    assert any(r.severity == "high" for r in results)

    # Anticoagulant + liver disease → high
    results = await get_condition_interactions([_med("warfarin")], ["liver disease"])
    assert any(r.severity == "high" for r in results)

    # Corticosteroid + diabetes → medium
    results = await get_condition_interactions([_med("prednisone")], ["diabetes"])
    assert any(r.severity == "medium" for r in results)


async def test_no_interaction_returns_empty():
    # Two drugs with no known class interaction rule
    results = await get_interactions([_med("metformin")], _med("omeprazole"))
    assert results == []

    # Unknown drug returns empty
    results = await get_interactions([_med("aspirin")], _med("somefakedrug"))
    assert results == []

    # No conditions → empty
    results = await get_condition_interactions([_med("warfarin")], [])
    assert results == []
