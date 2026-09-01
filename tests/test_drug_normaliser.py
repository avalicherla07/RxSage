from services.drug_normaliser import normalise_drug_name


def test_brand_to_generic_mapping():
    assert normalise_drug_name("Tylenol") == "acetaminophen"
    assert normalise_drug_name("Coumadin") == "warfarin"
    assert normalise_drug_name("Prozac") == "fluoxetine"
    assert normalise_drug_name("Zoloft") == "sertraline"

def test_dosage_stripping():
    assert normalise_drug_name("ibuprofen 400mg") == "ibuprofen"
    assert normalise_drug_name("Warfarin 5mg daily") == "warfarin"
    assert normalise_drug_name("metformin 500mg tablet") == "metformin"

def test_edge_cases():
    assert normalise_drug_name("") == ""
    assert normalise_drug_name("somefakedrug") == "somefakedrug"
    assert normalise_drug_name("ADVIL") == "ibuprofen"
    assert normalise_drug_name("  Lipitor  ") == "atorvastatin"
