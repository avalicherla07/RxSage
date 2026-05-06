"""Clinical test scenarios for RxGuide accuracy validation."""

SCENARIOS = [
    # ── LOCAL ANESTHETIC + VASOCONSTRICTOR ───────────────────────────────────
    {
        "id": "epi-beta-blocker",
        "name": "Epinephrine + non-selective beta-blocker",
        "description": "Carvedilol blocks beta-2 vasodilation, leaving alpha-1 unopposed. Risk of acute hypertensive crisis and reflex bradycardia.",
        "expected_risk": "high",
        "expected_keywords": ["beta", "epinephrine", "hypertension", "blood pressure", "vasoconstrict"],
        "request": {
            "patient": {"age": 67, "sex": "male", "conditions": ["hypertension", "heart failure"], "allergies": []},
            "current_medications": [{"name": "Carvedilol", "dosage": "25mg"}, {"name": "Furosemide", "dosage": "40mg"}],
            "candidate_medication": {"name": "Lidocaine with epinephrine", "dosage": "1.8ml cartridge 1:100000"},
            "procedure": {"type": "extraction", "complexity": "routine"},
        },
    },
    {
        "id": "epi-tricyclic",
        "name": "Epinephrine + tricyclic antidepressant",
        "description": "Amitriptyline blocks norepinephrine reuptake — epinephrine accumulates at adrenergic receptors, amplifying cardiovascular effects 2-3x.",
        "expected_risk": "high",
        "expected_keywords": ["tricyclic", "antidepressant", "cardiovascular", "epinephrine", "adrenergic"],
        "request": {
            "patient": {"age": 54, "sex": "female", "conditions": ["depression", "chronic pain"], "allergies": []},
            "current_medications": [{"name": "Amitriptyline", "dosage": "75mg"}],
            "candidate_medication": {"name": "Lidocaine with epinephrine", "dosage": "1.8ml cartridge 1:100000"},
        },
    },
    {
        "id": "lidocaine-cimetidine",
        "name": "Lidocaine + cimetidine",
        "description": "Cimetidine inhibits hepatic oxidative enzymes needed to metabolise lidocaine, raising plasma levels and toxicity risk.",
        "expected_risk": "high",
        "expected_keywords": ["cimetidine", "lidocaine", "toxicity", "metabolism", "hepatic"],
        "request": {
            "patient": {"age": 58, "sex": "male", "conditions": ["GERD", "peptic ulcer"], "allergies": []},
            "current_medications": [{"name": "Cimetidine", "dosage": "400mg"}],
            "candidate_medication": {"name": "Lidocaine", "dosage": "2% solution"},
        },
    },
    {
        "id": "epi-digoxin",
        "name": "Epinephrine + digoxin",
        "description": "Digoxin sensitises the myocardium — combined with epinephrine can trigger serious cardiac arrhythmias.",
        "expected_risk": "high",
        "expected_keywords": ["digoxin", "arrhythmia", "cardiac", "epinephrine", "myocardium"],
        "request": {
            "patient": {"age": 72, "sex": "female", "conditions": ["atrial fibrillation", "heart failure"], "allergies": []},
            "current_medications": [{"name": "Digoxin", "dosage": "0.125mg"}, {"name": "Furosemide", "dosage": "40mg"}],
            "candidate_medication": {"name": "Lidocaine with epinephrine", "dosage": "1.8ml cartridge 1:100000"},
        },
    },
    # ── ANTIBIOTIC INTERACTIONS ───────────────────────────────────────────────
    {
        "id": "metronidazole-warfarin",
        "name": "Metronidazole + warfarin",
        "description": "Metronidazole inhibits CYP2C9, the primary enzyme that breaks down warfarin. INR can double or triple within days causing fatal bleeding.",
        "expected_risk": "high",
        "expected_keywords": ["warfarin", "INR", "bleeding", "CYP2C9", "metronidazole", "anticoagul"],
        "request": {
            "patient": {"age": 68, "sex": "male", "conditions": ["atrial fibrillation", "deep vein thrombosis"], "allergies": ["penicillin"]},
            "current_medications": [{"name": "Warfarin", "dosage": "5mg"}],
            "candidate_medication": {"name": "Metronidazole", "dosage": "400mg"},
            "procedure": {"type": "extraction", "complexity": "surgical"},
        },
    },
    {
        "id": "clarithromycin-statin",
        "name": "Clarithromycin + simvastatin",
        "description": "Clarithromycin strongly inhibits CYP3A4 causing statin levels to rise dramatically. Risk of rhabdomyolysis.",
        "expected_risk": "high",
        "expected_keywords": ["statin", "CYP3A4", "rhabdomyolysis", "clarithromycin", "muscle"],
        "request": {
            "patient": {"age": 61, "sex": "female", "conditions": ["hypercholesterolaemia", "hypertension"], "allergies": []},
            "current_medications": [{"name": "Simvastatin", "dosage": "40mg"}, {"name": "Amlodipine", "dosage": "5mg"}],
            "candidate_medication": {"name": "Clarithromycin", "dosage": "500mg"},
        },
    },
    {
        "id": "clarithromycin-qt",
        "name": "Clarithromycin + QT-prolonging drug",
        "description": "Macrolide antibiotics prolong QT interval. Combined with antipsychotics can trigger fatal Torsades de Pointes.",
        "expected_risk": "high",
        "expected_keywords": ["QT", "arrhythmia", "clarithromycin", "Torsades", "cardiac"],
        "request": {
            "patient": {"age": 45, "sex": "female", "conditions": ["schizophrenia"], "allergies": []},
            "current_medications": [{"name": "Haloperidol", "dosage": "5mg"}],
            "candidate_medication": {"name": "Clarithromycin", "dosage": "500mg"},
        },
    },
    {
        "id": "fluconazole-warfarin",
        "name": "Fluconazole + warfarin",
        "description": "Fluconazole is a potent CYP2C9 inhibitor. Even a single dose can significantly raise INR in anticoagulated patients.",
        "expected_risk": "high",
        "expected_keywords": ["warfarin", "INR", "fluconazole", "CYP2C9", "bleeding"],
        "request": {
            "patient": {"age": 74, "sex": "female", "conditions": ["atrial fibrillation", "oral candidiasis"], "allergies": []},
            "current_medications": [{"name": "Warfarin", "dosage": "4mg"}],
            "candidate_medication": {"name": "Fluconazole", "dosage": "150mg"},
        },
    },
    # ── ANALGESIC INTERACTIONS ────────────────────────────────────────────────
    {
        "id": "nsaid-lithium",
        "name": "Ibuprofen + lithium",
        "description": "NSAIDs inhibit renal prostaglandins, reducing lithium excretion. Lithium levels rise rapidly — narrow therapeutic index means toxicity is serious.",
        "expected_risk": "high",
        "expected_keywords": ["lithium", "toxicity", "renal", "NSAID", "ibuprofen", "excretion"],
        "request": {
            "patient": {"age": 38, "sex": "male", "conditions": ["bipolar disorder"], "allergies": []},
            "current_medications": [{"name": "Lithium carbonate", "dosage": "400mg"}],
            "candidate_medication": {"name": "Ibuprofen", "dosage": "400mg"},
        },
    },
    {
        "id": "nsaid-methotrexate",
        "name": "Ibuprofen + high-dose methotrexate",
        "description": "NSAIDs reduce renal clearance of methotrexate. At high doses this can be life-threatening.",
        "expected_risk": "high",
        "expected_keywords": ["methotrexate", "renal", "clearance", "NSAID", "toxicity"],
        "request": {
            "patient": {"age": 52, "sex": "female", "conditions": ["rheumatoid arthritis"], "allergies": []},
            "current_medications": [{"name": "Methotrexate", "dosage": "15mg weekly"}],
            "candidate_medication": {"name": "Ibuprofen", "dosage": "600mg"},
        },
    },
    {
        "id": "opioid-benzo",
        "name": "Codeine + benzodiazepine",
        "description": "CNS depression is additive. Combined sedation can cause respiratory depression and death.",
        "expected_risk": "high",
        "expected_keywords": ["respiratory", "sedation", "CNS", "benzodiazepine", "opioid", "depression"],
        "request": {
            "patient": {"age": 44, "sex": "male", "conditions": ["anxiety disorder", "insomnia"], "allergies": []},
            "current_medications": [{"name": "Diazepam", "dosage": "5mg"}, {"name": "Zolpidem", "dosage": "10mg"}],
            "candidate_medication": {"name": "Codeine phosphate", "dosage": "30mg"},
        },
    },
    {
        "id": "codeine-ssri",
        "name": "Codeine + fluoxetine (CYP2D6 inhibitor)",
        "description": "Fluoxetine blocks CYP2D6, preventing codeine converting to morphine — making it ineffective and potentially toxic.",
        "expected_risk": "medium",
        "expected_risk_alt": "high",
        "expected_keywords": ["CYP2D6", "codeine", "fluoxetine", "metabolism", "SSRI"],
        "request": {
            "patient": {"age": 33, "sex": "female", "conditions": ["depression"], "allergies": []},
            "current_medications": [{"name": "Fluoxetine", "dosage": "20mg"}],
            "candidate_medication": {"name": "Codeine phosphate", "dosage": "30mg"},
        },
    },
    # ── SPECIALTY MEDICATION INTERACTIONS ────────────────────────────────────
    {
        "id": "bisphosphonate-extraction",
        "name": "Bisphosphonate + tooth extraction",
        "description": "Alendronate can trigger osteonecrosis of the jaw after invasive dental procedures (MRONJ).",
        "expected_risk": "high",
        "expected_keywords": ["bisphosphonate", "osteonecrosis", "jaw", "MRONJ", "extraction", "bone"],
        "request": {
            "patient": {"age": 69, "sex": "female", "conditions": ["osteoporosis"], "allergies": []},
            "current_medications": [{"name": "Alendronate", "dosage": "70mg weekly"}],
            "candidate_medication": {"name": "Tooth extraction procedure", "dosage": "N/A"},
        },
    },
    {
        "id": "ppi-implant",
        "name": "Proton pump inhibitor + dental implant",
        "description": "PPIs reduce calcium absorption and bone density. Studies show higher implant failure rates in PPI users.",
        "expected_risk": "medium",
        "expected_keywords": ["PPI", "implant", "bone", "calcium", "omeprazole", "failure"],
        "request": {
            "patient": {"age": 55, "sex": "male", "conditions": ["GERD"], "allergies": []},
            "current_medications": [{"name": "Omeprazole", "dosage": "20mg"}],
            "candidate_medication": {"name": "Dental implant procedure", "dosage": "N/A"},
        },
    },
    {
        "id": "immunosuppressant-infection",
        "name": "Tacrolimus + dental infection",
        "description": "Transplant immunosuppressants allow dental infections to become life-threatening. Also causes gingival overgrowth.",
        "expected_risk": "high",
        "expected_keywords": ["immunosuppressant", "tacrolimus", "infection", "transplant", "gingival"],
        "request": {
            "patient": {"age": 48, "sex": "male", "conditions": ["kidney transplant", "dental abscess"], "allergies": []},
            "current_medications": [{"name": "Tacrolimus", "dosage": "3mg"}, {"name": "Mycophenolate mofetil", "dosage": "500mg"}],
            "candidate_medication": {"name": "Amoxicillin", "dosage": "500mg"},
        },
    },
    {
        "id": "ssri-nsaid-bleeding",
        "name": "SSRI + NSAID bleeding risk",
        "description": "SSRIs deplete platelet serotonin impairing aggregation. NSAIDs add antiplatelet effect — combined bleeding risk is elevated.",
        "expected_risk": "medium",
        "expected_keywords": ["SSRI", "bleeding", "platelet", "NSAID", "serotonin", "aggregation"],
        "request": {
            "patient": {"age": 42, "sex": "female", "conditions": ["depression", "chronic pain"], "allergies": []},
            "current_medications": [{"name": "Sertraline", "dosage": "100mg"}],
            "candidate_medication": {"name": "Ibuprofen", "dosage": "400mg"},
        },
    },
    {
        "id": "oral-manifestations-polypharmacy",
        "name": "Oral manifestations — mental health polypharmacy",
        "description": "Patient on multiple mental health medications. Service should surface oral side effects.",
        "expected_risk": "low",
        "expected_risk_alt": "medium",
        "expected_keywords": ["xerostomia"],
        "request": {
            "patient": {"age": 34, "sex": "female", "conditions": ["depression", "anxiety", "ADHD"], "allergies": []},
            "current_medications": [
                {"name": "Sertraline", "dosage": "100mg"},
                {"name": "Quetiapine", "dosage": "50mg"},
                {"name": "Amphetamine salts", "dosage": "20mg"}
            ],
            "candidate_medication": {"name": "Lidocaine with epinephrine", "dosage": "1.8ml 1:100000"},
            "sedation_requested": True,
            "sedation_agent_requested": "Valium",
        },
    },
    # ── NEW SOURCE VERIFICATION ──────────────────────────────────────────────
    {
        "id": "kegg-cyp-clarithromycin-simvastatin",
        "name": "KEGG — clarithromycin + simvastatin CYP interaction",
        "description": "Clarithromycin is a strong CYP3A4 inhibitor. Simvastatin is a CYP3A4 substrate. KEGG should flag this.",
        "expected_risk": "high",
        "expected_keywords": ["CYP3A4", "simvastatin", "clarithromycin", "statin"],
        "request": {
            "patient": {"age": 58, "sex": "male", "conditions": ["hypercholesterolaemia", "dental infection"], "allergies": ["penicillin"]},
            "current_medications": [{"name": "simvastatin", "dosage": "40mg"}],
            "candidate_medication": {"name": "clarithromycin", "dosage": "500mg"},
        },
    },
    {
        "id": "medlineplus-stjohnswort-ssri",
        "name": "MedlinePlus — St. John's Wort + sertraline supplement risk",
        "description": "St. John's Wort causes serotonin syndrome risk with SSRIs. MedlinePlus covers this.",
        "expected_risk": "medium",
        "expected_risk_alt": "high",
        "expected_keywords": ["serotonin", "sertraline"],
        "request": {
            "patient": {"age": 35, "sex": "female", "conditions": ["depression"], "allergies": []},
            "current_medications": [{"name": "sertraline", "dosage": "100mg"}],
            "candidate_medication": {"name": "ibuprofen", "dosage": "400mg"},
            "supplements": [{"name": "St. John's Wort", "dose": "300mg", "type": "herbal"}],
        },
    },
]
