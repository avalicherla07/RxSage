"""Local drug interaction database — curated high-severity interactions.

Covers clinically significant drug-drug interactions relevant to dental
practice. Organized by pharmacological class pairs with specific drug
name mappings. Instant lookup, no API calls, no rate limits.

Sources: FDA drug labels, ADA dental drug interaction guidelines,
clinical pharmacology references, Lexicomp interaction data.
"""
from __future__ import annotations

import logging
from models.request import MedicationInput
from models.response import RxNavInteraction

logger = logging.getLogger(__name__)

_SOURCE_URL = "https://dailymed.nlm.nih.gov/"

# ═══════════════════════════════════════════════════════════════════════════
# DRUG CLASS MAPPING — maps generic drug names to pharmacological classes
# ═══════════════════════════════════════════════════════════════════════════

_DRUG_CLASSES: dict[str, list[str]] = {
    # ── Anticoagulants / Antithrombotics ──
    "warfarin": ["anticoagulant", "vitamin_k_antagonist"],
    "heparin": ["anticoagulant"],
    "enoxaparin": ["anticoagulant", "lmwh"],
    "rivaroxaban": ["anticoagulant", "doac"],
    "apixaban": ["anticoagulant", "doac", "cyp3a4_substrate"],
    "dabigatran": ["anticoagulant", "doac"],
    "edoxaban": ["anticoagulant", "doac"],
    "clopidogrel": ["antiplatelet"],
    "prasugrel": ["antiplatelet"],
    "ticagrelor": ["antiplatelet"],
    "aspirin": ["nsaid", "antiplatelet"],
    "dipyridamole": ["antiplatelet"],

    # ── NSAIDs ──
    "ibuprofen": ["nsaid"],
    "naproxen": ["nsaid"],
    "diclofenac": ["nsaid"],
    "celecoxib": ["nsaid", "cox2_inhibitor"],
    "meloxicam": ["nsaid"],
    "ketorolac": ["nsaid"],
    "indomethacin": ["nsaid"],
    "piroxicam": ["nsaid"],
    "mefenamic acid": ["nsaid"],

    # ── Antibiotics ──
    "amoxicillin": ["antibiotic", "penicillin"],
    "ampicillin": ["antibiotic", "penicillin"],
    "penicillin": ["antibiotic", "penicillin"],
    "clindamycin": ["antibiotic", "lincosamide"],
    "metronidazole": ["antibiotic", "nitroimidazole", "cyp2c9_inhibitor"],
    "azithromycin": ["antibiotic", "macrolide"],
    "erythromycin": ["antibiotic", "macrolide", "cyp3a4_inhibitor", "qt_prolonging"],
    "clarithromycin": ["antibiotic", "macrolide", "cyp3a4_inhibitor", "qt_prolonging"],
    "ciprofloxacin": ["antibiotic", "fluoroquinolone", "cyp1a2_inhibitor"],
    "levofloxacin": ["antibiotic", "fluoroquinolone", "qt_prolonging"],
    "moxifloxacin": ["antibiotic", "fluoroquinolone", "qt_prolonging"],
    "doxycycline": ["antibiotic", "tetracycline"],
    "tetracycline": ["antibiotic", "tetracycline"],
    "minocycline": ["antibiotic", "tetracycline"],
    "trimethoprim": ["antibiotic"],
    "sulfamethoxazole": ["antibiotic"],

    # ── Antifungals ──
    "fluconazole": ["antifungal", "cyp2c9_inhibitor", "cyp3a4_inhibitor"],
    "itraconazole": ["antifungal", "cyp3a4_inhibitor"],
    "ketoconazole": ["antifungal", "cyp3a4_inhibitor"],
    "nystatin": ["antifungal"],
    "clotrimazole": ["antifungal"],

    # ── Antihypertensives ──
    "lisinopril": ["ace_inhibitor", "antihypertensive"],
    "enalapril": ["ace_inhibitor", "antihypertensive"],
    "ramipril": ["ace_inhibitor", "antihypertensive"],
    "losartan": ["arb", "antihypertensive"],
    "valsartan": ["arb", "antihypertensive"],
    "irbesartan": ["arb", "antihypertensive"],
    "amlodipine": ["ccb", "antihypertensive"],
    "nifedipine": ["ccb", "antihypertensive"],
    "diltiazem": ["ccb", "antihypertensive", "cyp3a4_inhibitor"],
    "verapamil": ["ccb", "antihypertensive", "cyp3a4_inhibitor"],
    "metoprolol": ["beta_blocker", "antihypertensive"],
    "atenolol": ["beta_blocker", "antihypertensive"],
    "propranolol": ["beta_blocker", "antihypertensive", "nonselective_beta_blocker"],
    "carvedilol": ["beta_blocker", "antihypertensive", "nonselective_beta_blocker"],
    "nadolol": ["beta_blocker", "antihypertensive", "nonselective_beta_blocker"],
    "labetalol": ["beta_blocker", "antihypertensive", "nonselective_beta_blocker"],
    "furosemide": ["diuretic", "loop_diuretic"],
    "hydrochlorothiazide": ["diuretic", "thiazide"],
    "spironolactone": ["diuretic", "potassium_sparing"],

    # ── Cardiac glycosides ──
    "digoxin": ["cardiac_glycoside", "arrhythmia_sensitive"],

    # ── Diabetes ──
    "metformin": ["antidiabetic", "biguanide"],
    "glipizide": ["antidiabetic", "sulfonylurea"],
    "glyburide": ["antidiabetic", "sulfonylurea"],
    "glimepiride": ["antidiabetic", "sulfonylurea"],
    "insulin": ["antidiabetic", "insulin"],
    "sitagliptin": ["antidiabetic"],
    "empagliflozin": ["antidiabetic", "sglt2_inhibitor"],

    # ── SSRIs / SNRIs / Antidepressants ──
    "sertraline": ["ssri", "antidepressant", "serotonergic"],
    "fluoxetine": ["ssri", "antidepressant", "cyp2d6_inhibitor", "serotonergic"],
    "paroxetine": ["ssri", "antidepressant", "cyp2d6_inhibitor", "serotonergic"],
    "citalopram": ["ssri", "antidepressant", "serotonergic", "qt_prolonging"],
    "escitalopram": ["ssri", "antidepressant", "serotonergic", "qt_prolonging"],
    "venlafaxine": ["snri", "antidepressant", "serotonergic"],
    "duloxetine": ["snri", "antidepressant", "serotonergic"],

    # ── Tricyclic antidepressants ──
    "amitriptyline": ["tca", "antidepressant", "norepinephrine_reuptake_inhibitor", "qt_prolonging"],
    "nortriptyline": ["tca", "antidepressant", "norepinephrine_reuptake_inhibitor"],
    "imipramine": ["tca", "antidepressant", "norepinephrine_reuptake_inhibitor", "qt_prolonging"],
    "desipramine": ["tca", "antidepressant", "norepinephrine_reuptake_inhibitor"],
    "doxepin": ["tca", "antidepressant", "norepinephrine_reuptake_inhibitor"],

    # ── MAOIs ──
    "phenelzine": ["maoi", "antidepressant"],
    "tranylcypromine": ["maoi", "antidepressant"],
    "selegiline": ["maoi"],

    # ── Antipsychotics ──
    "haloperidol": ["antipsychotic", "qt_prolonging"],
    "chlorpromazine": ["antipsychotic", "qt_prolonging"],
    "quetiapine": ["antipsychotic", "qt_prolonging"],
    "risperidone": ["antipsychotic"],
    "olanzapine": ["antipsychotic"],
    "aripiprazole": ["antipsychotic"],
    "ziprasidone": ["antipsychotic", "qt_prolonging"],

    # ── Benzodiazepines / Sedatives ──
    "diazepam": ["benzodiazepine", "sedative", "cns_depressant"],
    "midazolam": ["benzodiazepine", "sedative", "cns_depressant", "cyp3a4_substrate"],
    "triazolam": ["benzodiazepine", "sedative", "cns_depressant", "cyp3a4_substrate"],
    "lorazepam": ["benzodiazepine", "sedative", "cns_depressant"],
    "alprazolam": ["benzodiazepine", "sedative", "cns_depressant", "cyp3a4_substrate"],
    "zolpidem": ["sedative", "cns_depressant"],
    "zopiclone": ["sedative", "cns_depressant"],

    # ── Opioids ──
    "codeine": ["opioid", "analgesic", "cns_depressant", "cyp2d6_substrate"],
    "codeine phosphate": ["opioid", "analgesic", "cns_depressant", "cyp2d6_substrate"],
    "hydrocodone": ["opioid", "analgesic", "cns_depressant"],
    "oxycodone": ["opioid", "analgesic", "cns_depressant"],
    "tramadol": ["opioid", "analgesic", "cns_depressant", "serotonergic"],
    "fentanyl": ["opioid", "analgesic", "cns_depressant"],
    "morphine": ["opioid", "analgesic", "cns_depressant"],
    "meperidine": ["opioid", "analgesic", "cns_depressant", "serotonergic"],

    # ── Corticosteroids ──
    "prednisone": ["corticosteroid"],
    "prednisolone": ["corticosteroid"],
    "dexamethasone": ["corticosteroid"],
    "hydrocortisone": ["corticosteroid"],
    "methylprednisolone": ["corticosteroid"],

    # ── Statins ──
    "atorvastatin": ["statin", "cyp3a4_substrate"],
    "simvastatin": ["statin", "cyp3a4_substrate"],
    "rosuvastatin": ["statin"],
    "lovastatin": ["statin", "cyp3a4_substrate"],
    "pravastatin": ["statin"],

    # ── PPIs / H2 blockers ──
    "omeprazole": ["ppi", "cyp2c19_inhibitor"],
    "pantoprazole": ["ppi"],
    "esomeprazole": ["ppi", "cyp2c19_inhibitor"],
    "lansoprazole": ["ppi"],
    "cimetidine": ["h2_blocker", "cyp_inhibitor_broad"],
    "ranitidine": ["h2_blocker"],
    "famotidine": ["h2_blocker"],

    # ── Local anesthetics (dental) ──
    "lidocaine": ["local_anesthetic", "cyp_hepatic_substrate"],
    "lidocaine with epinephrine": ["local_anesthetic", "cyp_hepatic_substrate", "vasoconstrictor", "sympathomimetic"],
    "articaine": ["local_anesthetic"],
    "bupivacaine": ["local_anesthetic"],
    "mepivacaine": ["local_anesthetic"],
    "prilocaine": ["local_anesthetic"],

    # ── Vasoconstrictors (dental) ──
    "epinephrine": ["vasoconstrictor", "sympathomimetic"],

    # ── Lithium ──
    "lithium": ["lithium", "narrow_therapeutic_index"],
    "lithium carbonate": ["lithium", "narrow_therapeutic_index"],

    # ── Methotrexate ──
    "methotrexate": ["methotrexate", "immunosuppressant", "narrow_therapeutic_index"],

    # ── Bisphosphonates ──
    "alendronate": ["bisphosphonate", "bone_resorption_inhibitor"],
    "risedronate": ["bisphosphonate", "bone_resorption_inhibitor"],
    "zoledronic acid": ["bisphosphonate", "bone_resorption_inhibitor", "iv_bisphosphonate"],
    "ibandronate": ["bisphosphonate", "bone_resorption_inhibitor"],
    "denosumab": ["bone_resorption_inhibitor"],

    # ── Immunosuppressants ──
    "tacrolimus": ["immunosuppressant", "calcineurin_inhibitor", "narrow_therapeutic_index"],
    "cyclosporine": ["immunosuppressant", "calcineurin_inhibitor", "narrow_therapeutic_index"],
    "mycophenolate mofetil": ["immunosuppressant"],
    "mycophenolate": ["immunosuppressant"],
    "azathioprine": ["immunosuppressant"],
    "sirolimus": ["immunosuppressant"],

    # ── Anticonvulsants ──
    "phenytoin": ["anticonvulsant", "narrow_therapeutic_index", "cyp_inducer"],
    "carbamazepine": ["anticonvulsant", "cyp_inducer", "cyp3a4_inducer"],
    "valproic acid": ["anticonvulsant"],
    "gabapentin": ["anticonvulsant"],
    "pregabalin": ["anticonvulsant"],
    "lamotrigine": ["anticonvulsant"],
    "levetiracetam": ["anticonvulsant"],

    # ── Dental procedures (special entries) ──
    "tooth extraction procedure": ["invasive_dental_procedure"],
    "dental implant procedure": ["invasive_dental_procedure", "bone_dependent_procedure"],
    "dental surgery": ["invasive_dental_procedure"],
}


# ═══════════════════════════════════════════════════════════════════════════
# CLASS INTERACTION RULES
# Each rule: (classes_a, classes_b, severity, description)
# A match occurs when drug A has any class in classes_a AND drug B has any
# class in classes_b (checked in both directions).
# ═══════════════════════════════════════════════════════════════════════════

_CLASS_INTERACTIONS: list[tuple[set[str], set[str], str, str]] = [

    # ── ANTICOAGULANT INTERACTIONS ──────────────────────────────────────────

    ({"anticoagulant"}, {"nsaid"}, "high",
     "NSAIDs may significantly increase bleeding risk when combined with anticoagulants. "
     "NSAIDs inhibit platelet function and may cause GI bleeding. This combination could "
     "lead to serious or life-threatening hemorrhage. Consider acetaminophen as an alternative."),

    ({"anticoagulant"}, {"antiplatelet"}, "high",
     "Combining anticoagulants with antiplatelet agents significantly increases bleeding risk. "
     "Monitor for signs of bleeding during and after dental procedures."),

    ({"vitamin_k_antagonist"}, {"nitroimidazole"}, "high",
     "Metronidazole inhibits CYP2C9, the primary enzyme that metabolises warfarin. "
     "INR can double or triple within days, causing potentially fatal bleeding. "
     "Monitor INR closely or consider alternative antibiotics."),

    ({"vitamin_k_antagonist"}, {"cyp2c9_inhibitor"}, "high",
     "CYP2C9 inhibitors (fluconazole, metronidazole) may significantly increase warfarin "
     "levels by blocking its primary metabolic pathway. INR may rise dangerously. "
     "Monitor INR closely and consider dose reduction."),

    ({"vitamin_k_antagonist"}, {"macrolide"}, "high",
     "Macrolide antibiotics (erythromycin, clarithromycin) may increase warfarin levels by "
     "inhibiting CYP3A4 metabolism, potentially leading to elevated INR and bleeding risk. "
     "Consider azithromycin (lower interaction potential) or monitor INR closely."),

    ({"vitamin_k_antagonist"}, {"fluoroquinolone"}, "medium",
     "Fluoroquinolones may enhance the anticoagulant effect of warfarin. Monitor INR if "
     "ciprofloxacin or similar agents are prescribed concurrently."),

    # ── NSAID INTERACTIONS ──────────────────────────────────────────────────

    ({"nsaid"}, {"ace_inhibitor"}, "medium",
     "NSAIDs may reduce the antihypertensive effect of ACE inhibitors and increase the risk "
     "of renal impairment. Blood pressure monitoring may be warranted."),

    ({"nsaid"}, {"arb"}, "medium",
     "NSAIDs may reduce the antihypertensive effect of ARBs and increase the risk of renal "
     "impairment, particularly in patients with existing renal compromise."),

    ({"nsaid"}, {"ssri"}, "medium",
     "SSRIs deplete platelet serotonin, impairing aggregation. Combined with NSAIDs, "
     "there is a significantly elevated risk of GI bleeding. Consider gastroprotective "
     "therapy or acetaminophen as an alternative analgesic."),

    ({"nsaid"}, {"snri"}, "medium",
     "SNRIs may impair platelet function similarly to SSRIs. Combined with NSAIDs, "
     "bleeding risk may be elevated. Consider gastroprotective measures."),

    ({"nsaid"}, {"corticosteroid"}, "medium",
     "Concurrent use of NSAIDs and corticosteroids may increase the risk of GI ulceration "
     "and bleeding. Consider gastroprotective measures."),

    ({"nsaid"}, {"lithium"}, "high",
     "NSAIDs inhibit renal prostaglandins, reducing lithium excretion. Lithium has a narrow "
     "therapeutic index — levels can rise rapidly to toxic concentrations. This combination "
     "may cause serious lithium toxicity. Consider acetaminophen instead."),

    ({"nsaid"}, {"methotrexate"}, "high",
     "NSAIDs reduce renal clearance of methotrexate, potentially causing life-threatening "
     "toxicity including bone marrow suppression and renal failure. Avoid this combination "
     "especially with high-dose methotrexate. Consider acetaminophen."),

    ({"nsaid"}, {"diuretic"}, "medium",
     "NSAIDs may reduce the effectiveness of diuretics and increase the risk of renal "
     "impairment, particularly in elderly patients or those with heart failure."),

    # ── OPIOID / CNS DEPRESSANT INTERACTIONS ────────────────────────────────

    ({"opioid"}, {"benzodiazepine"}, "high",
     "Concurrent use of opioids and benzodiazepines may result in profound sedation, "
     "respiratory depression, coma, or death. FDA black box warning. Use the lowest "
     "effective doses and shortest duration if combination is necessary."),

    ({"opioid"}, {"sedative"}, "high",
     "Combining opioids with sedative-hypnotics (including zolpidem) increases the risk "
     "of profound CNS depression and respiratory failure. Avoid if possible."),

    ({"opioid"}, {"serotonergic"}, "medium",
     "Combining opioids (especially tramadol, meperidine) with serotonergic drugs "
     "(SSRIs, SNRIs) may increase the risk of serotonin syndrome. Monitor for agitation, "
     "confusion, rapid heart rate, and muscle rigidity."),

    ({"cyp2d6_substrate"}, {"cyp2d6_inhibitor"}, "medium",
     "CYP2D6 inhibitors (fluoxetine, paroxetine) block the conversion of codeine to "
     "morphine, making codeine ineffective for pain relief. Toxic codeine metabolites "
     "may also accumulate. Consider alternative analgesics."),

    ({"opioid"}, {"maoi"}, "high",
     "Combining opioids with MAOIs can cause serotonin syndrome, severe respiratory "
     "depression, or hypertensive crisis. This combination is contraindicated. "
     "Wait at least 14 days after stopping an MAOI before prescribing opioids."),

    # ── LOCAL ANESTHETIC / VASOCONSTRICTOR INTERACTIONS ─────────────────────

    ({"local_anesthetic"}, {"beta_blocker"}, "medium",
     "Beta-blockers may reduce hepatic metabolism of local anesthetics (especially lidocaine), "
     "potentially increasing plasma levels and risk of toxicity. Use lower doses."),

    ({"sympathomimetic"}, {"nonselective_beta_blocker"}, "high",
     "Epinephrine in dental anesthetics combined with non-selective beta-blockers (propranolol, "
     "carvedilol, nadolol) may cause acute hypertensive crisis and reflex bradycardia. "
     "Beta-2 vasodilation is blocked, leaving alpha-1 vasoconstriction unopposed. "
     "Use minimal epinephrine or consider mepivacaine without vasoconstrictor."),

    ({"sympathomimetic"}, {"beta_blocker"}, "medium",
     "Epinephrine in dental anesthetics may interact with beta-blockers. While selective "
     "beta-blockers (metoprolol, atenolol) carry lower risk than non-selective agents, "
     "blood pressure monitoring is still recommended. Use minimal epinephrine and aspirate."),

    ({"sympathomimetic"}, {"tca"}, "high",
     "Tricyclic antidepressants block norepinephrine reuptake — epinephrine accumulates at "
     "adrenergic receptors, amplifying cardiovascular effects 2-3x. Risk of severe "
     "hypertension and cardiac arrhythmias. Use minimal epinephrine with aspiration."),

    ({"sympathomimetic"}, {"maoi"}, "high",
     "MAOIs prevent breakdown of catecholamines. Epinephrine in dental anesthetics may "
     "cause severe hypertensive crisis. Avoid epinephrine-containing anesthetics entirely."),

    ({"sympathomimetic"}, {"cardiac_glycoside"}, "high",
     "Digoxin sensitises the myocardium to catecholamines. Combined with epinephrine, "
     "this may trigger serious cardiac arrhythmias including ventricular fibrillation. "
     "Use minimal epinephrine concentration and monitor cardiac rhythm."),

    ({"cyp_hepatic_substrate"}, {"cyp_inhibitor_broad"}, "high",
     "Cimetidine broadly inhibits hepatic CYP enzymes required to metabolise lidocaine, "
     "raising plasma lidocaine levels and increasing risk of CNS toxicity (tinnitus, "
     "perioral numbness, seizures). Use lowest effective lidocaine dose."),

    # ── CYP3A4 INTERACTIONS ─────────────────────────────────────────────────

    ({"cyp3a4_inhibitor"}, {"cyp3a4_substrate"}, "high",
     "CYP3A4 inhibitors (erythromycin, clarithromycin, fluconazole, itraconazole, "
     "diltiazem, verapamil) may significantly increase plasma levels of CYP3A4 substrates "
     "(midazolam, triazolam, alprazolam, simvastatin, atorvastatin), leading to excessive "
     "sedation or rhabdomyolysis. Consider alternative agents."),

    ({"cyp3a4_inhibitor"}, {"statin"}, "high",
     "CYP3A4 inhibitors may dramatically increase statin levels, raising the risk of "
     "rhabdomyolysis. Most relevant for simvastatin and lovastatin. Consider rosuvastatin "
     "or pravastatin as alternatives (not CYP3A4 dependent)."),

    # ── QT PROLONGATION ─────────────────────────────────────────────────────

    ({"qt_prolonging"}, {"qt_prolonging"}, "high",
     "Combining two QT-prolonging drugs significantly increases the risk of fatal cardiac "
     "arrhythmias (Torsades de Pointes). Macrolide antibiotics + antipsychotics, or "
     "macrolides + certain SSRIs, are particularly dangerous combinations. "
     "Consider alternative antibiotics (amoxicillin, clindamycin) that do not prolong QT."),

    # ── BISPHOSPHONATE / BONE INTERACTIONS ──────────────────────────────────

    ({"bisphosphonate"}, {"invasive_dental_procedure"}, "high",
     "Bisphosphonates (alendronate, risedronate, zoledronic acid) may cause medication-related "
     "osteonecrosis of the jaw (MRONJ) after invasive dental procedures including extractions, "
     "implant placement, and periodontal surgery. Risk is highest with IV bisphosphonates "
     "and long-duration oral therapy (>3 years). Consult prescribing physician before proceeding."),

    ({"bone_resorption_inhibitor"}, {"invasive_dental_procedure"}, "high",
     "Bone resorption inhibitors (bisphosphonates, denosumab) increase the risk of "
     "osteonecrosis of the jaw (MRONJ) after invasive dental procedures. "
     "Consider drug holiday consultation with prescribing physician."),

    ({"ppi"}, {"bone_dependent_procedure"}, "medium",
     "Long-term PPI use reduces calcium absorption and may decrease bone density. "
     "Studies show significantly higher dental implant failure rates in PPI users. "
     "Consider bone density assessment before implant placement."),

    # ── IMMUNOSUPPRESSANT INTERACTIONS ──────────────────────────────────────

    ({"immunosuppressant"}, {"antibiotic"}, "medium",
     "Immunosuppressed patients (transplant recipients on tacrolimus, cyclosporine) "
     "may have altered drug metabolism and increased infection risk. Dental infections "
     "can become life-threatening. Coordinate antibiotic selection with transplant team. "
     "Macrolide antibiotics may increase tacrolimus/cyclosporine levels via CYP3A4 inhibition."),

    ({"calcineurin_inhibitor"}, {"cyp3a4_inhibitor"}, "high",
     "CYP3A4 inhibitors (erythromycin, clarithromycin, fluconazole) may dramatically "
     "increase tacrolimus or cyclosporine levels, causing nephrotoxicity and neurotoxicity. "
     "Use azithromycin or clindamycin instead."),

    ({"calcineurin_inhibitor"}, {"nsaid"}, "high",
     "NSAIDs may significantly increase the nephrotoxic effects of calcineurin inhibitors "
     "(tacrolimus, cyclosporine). Avoid NSAIDs in transplant patients. Use acetaminophen."),

    # ── PPI / H2 BLOCKER INTERACTIONS ───────────────────────────────────────

    ({"ppi"}, {"antiplatelet"}, "medium",
     "PPIs (especially omeprazole, esomeprazole) may reduce the antiplatelet effect of "
     "clopidogrel by inhibiting CYP2C19 activation. Consider pantoprazole as an alternative."),

    ({"cyp_inhibitor_broad"}, {"local_anesthetic"}, "high",
     "Cimetidine inhibits multiple hepatic CYP enzymes, reducing lidocaine clearance and "
     "raising plasma levels. Risk of lidocaine toxicity (tinnitus, perioral numbness, "
     "seizures, cardiac arrest). Use lowest effective dose and avoid repeat cartridges."),

    # ── ANTICONVULSANT INTERACTIONS ─────────────────────────────────────────

    ({"cyp_inducer"}, {"anticoagulant"}, "medium",
     "CYP enzyme inducers (phenytoin, carbamazepine) may reduce warfarin levels, "
     "decreasing anticoagulant effect. INR monitoring is recommended."),

    ({"anticonvulsant"}, {"opioid"}, "medium",
     "Some anticonvulsants may alter opioid metabolism. Gabapentin and pregabalin "
     "combined with opioids increase CNS depression risk."),

    # ── TETRACYCLINE INTERACTIONS ───────────────────────────────────────────

    ({"tetracycline"}, {"antidiabetic"}, "low",
     "Tetracyclines may rarely enhance the hypoglycemic effect of antidiabetic agents. "
     "Monitor blood glucose if prescribing doxycycline to diabetic patients."),
]


# ═══════════════════════════════════════════════════════════════════════════
# DRUG-CLASS + PATIENT-CONDITION INTERACTION RULES
# Each rule: (drug_classes, condition_keywords, severity, description)
# Matches when a patient has a condition AND is taking a drug of that class.
# ═══════════════════════════════════════════════════════════════════════════

_CONDITION_INTERACTIONS: list[tuple[set[str], set[str], str, str]] = [

    # ── Immunosuppression + infection ──
    ({"immunosuppressant", "calcineurin_inhibitor"},
     {"transplant", "immunosuppressed", "immunocompromised"},
     "high",
     "Immunosuppressed patients (transplant recipients on tacrolimus, cyclosporine, "
     "mycophenolate) are at high risk for life-threatening dental infections. Dental "
     "abscesses can progress to sepsis rapidly. Coordinate antibiotic selection with "
     "transplant team. Macrolide antibiotics may increase calcineurin inhibitor levels."),

    ({"immunosuppressant"},
     {"dental abscess", "dental infection", "periapical abscess", "cellulitis"},
     "high",
     "Active dental infection in an immunosuppressed patient requires urgent treatment. "
     "Risk of systemic spread is significantly elevated. Consider IV antibiotics and "
     "physician consultation before invasive dental procedures."),

    ({"calcineurin_inhibitor"},
     {"gingival", "periodontal"},
     "medium",
     "Calcineurin inhibitors (tacrolimus, cyclosporine) commonly cause gingival overgrowth. "
     "This may complicate periodontal treatment and require medication adjustment "
     "in coordination with the prescribing physician."),

    # ── Anticoagulants + bleeding-prone conditions ──
    ({"anticoagulant"},
     {"liver disease", "hepatic impairment", "cirrhosis", "coagulopathy"},
     "high",
     "Anticoagulants in patients with liver disease carry extremely high bleeding risk "
     "due to impaired clotting factor synthesis. INR may be unreliable. "
     "Consult hematology before any invasive dental procedure."),

    ({"anticoagulant"},
     {"renal impairment", "kidney disease", "ckd", "dialysis"},
     "high",
     "Renal impairment affects anticoagulant clearance and platelet function. "
     "Bleeding risk is significantly elevated. Dose adjustment and close monitoring required."),

    # ── NSAIDs + renal/GI conditions ──
    ({"nsaid"},
     {"renal impairment", "kidney disease", "ckd", "dialysis"},
     "high",
     "NSAIDs are contraindicated in significant renal impairment — they reduce renal "
     "blood flow via prostaglandin inhibition, potentially causing acute kidney injury. "
     "Use acetaminophen instead."),

    ({"nsaid"},
     {"gi bleed", "peptic ulcer", "gastric ulcer", "gi bleeding history"},
     "high",
     "NSAIDs in patients with GI bleeding history carry high risk of recurrent hemorrhage. "
     "Avoid NSAIDs entirely. Use acetaminophen for pain management."),

    # ── Bisphosphonates + bone conditions ──
    ({"bisphosphonate", "bone_resorption_inhibitor"},
     {"osteoporosis", "bone metastasis", "paget", "myeloma"},
     "medium",
     "Long-term bisphosphonate use (>3 years oral, any duration IV) increases MRONJ risk "
     "with invasive dental procedures. Risk is higher with IV bisphosphonates and "
     "concurrent corticosteroid use. Consult prescribing physician about drug holiday."),

    # ── Corticosteroids + adrenal suppression ──
    ({"corticosteroid"},
     {"adrenal insufficiency", "addison", "long-term steroid", "steroid dependent"},
     "high",
     "Patients on long-term corticosteroids may have adrenal suppression. Stressful dental "
     "procedures may require supplemental corticosteroid dosing to prevent adrenal crisis. "
     "Consult prescribing physician for stress-dose protocol."),

    ({"corticosteroid"},
     {"diabetes", "diabetic"},
     "medium",
     "Corticosteroids elevate blood glucose. Diabetic patients on corticosteroids may need "
     "glucose monitoring during and after dental procedures, especially with sedation."),

    # ── Sedation risks in elderly/respiratory ──
    ({"opioid", "benzodiazepine", "cns_depressant"},
     {"copd", "sleep apnea", "respiratory disease", "asthma"},
     "high",
     "CNS depressants (opioids, benzodiazepines) in patients with respiratory disease "
     "carry high risk of respiratory depression. Use minimal sedation, avoid opioids "
     "if possible, and monitor oxygen saturation."),

    ({"opioid", "benzodiazepine", "cns_depressant"},
     {"elderly", "frail", "fall risk"},
     "high",
     "Elderly or frail patients are at increased risk of excessive sedation, falls, "
     "and respiratory depression with CNS depressants. Use lowest effective doses."),

    # ── Anticonvulsants + dental ──
    ({"anticonvulsant"},
     {"epilepsy", "seizure disorder"},
     "medium",
     "Dental procedures may trigger seizures in epileptic patients, especially with stress "
     "or missed medication doses. Ensure patient has taken anticonvulsant medication. "
     "Have seizure management protocol ready."),

    # ── Phenytoin / cyclosporine gingival effects ──
    ({"anticonvulsant"},
     {"gingival hyperplasia", "gingival overgrowth"},
     "medium",
     "Phenytoin and some other anticonvulsants cause gingival hyperplasia. "
     "Meticulous oral hygiene and regular periodontal care are essential. "
     "Consider discussing medication alternatives with neurologist."),

    # ── Diabetes + infection risk ──
    ({"antidiabetic"},
     {"uncontrolled diabetes", "hba1c elevated", "poorly controlled diabetes"},
     "medium",
     "Poorly controlled diabetes increases infection risk and impairs wound healing "
     "after dental procedures. Consider delaying elective procedures until glycemic "
     "control improves. Prophylactic antibiotics may be warranted."),

    # ── Cardiac conditions + epinephrine ──
    ({"vasoconstrictor", "sympathomimetic"},
     {"arrhythmia", "atrial fibrillation", "ventricular tachycardia", "heart failure"},
     "high",
     "Epinephrine in dental anesthetics may exacerbate cardiac arrhythmias in patients "
     "with pre-existing cardiac conditions. Use minimal epinephrine concentration, "
     "aspirate before injection, and limit to 2 cartridges maximum."),
]


# ═══════════════════════════════════════════════════════════════════════════
# RISK AMPLIFICATION RULES — patient factors that elevate risk
# Each rule: (condition_keywords, amplification_factor, reason)
# Applied AFTER drug interactions are identified.
# ═══════════════════════════════════════════════════════════════════════════

_RISK_AMPLIFIERS: list[tuple[set[str], str, str]] = [
    ({"age_over_65"}, "age",
     "Patient age >65 increases risk of adverse drug reactions, bleeding, "
     "and sedation sensitivity."),
    ({"age_over_75"}, "age",
     "Patient age >75 significantly increases all drug interaction risks "
     "due to reduced hepatic/renal clearance."),
    ({"renal impairment", "kidney disease", "ckd", "dialysis"}, "renal",
     "Renal impairment reduces drug clearance, increasing plasma levels "
     "and toxicity risk for renally-cleared drugs."),
    ({"liver disease", "hepatic impairment", "cirrhosis"}, "hepatic",
     "Hepatic impairment reduces drug metabolism, increasing plasma levels "
     "and duration of action for hepatically-cleared drugs."),
    ({"polypharmacy"}, "polypharmacy",
     "Patient is on 5+ medications — interaction probability increases "
     "exponentially with medication count."),
    ({"pregnancy", "pregnant"}, "pregnancy",
     "Many dental drugs are contraindicated or require dose adjustment in pregnancy."),
    ({"breastfeeding", "lactating"}, "lactation",
     "Drug transfer to breast milk must be considered for all prescriptions."),
]


# ═══════════════════════════════════════════════════════════════════════════
# LOOKUP FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def _get_drug_classes(name: str) -> set[str]:
    """Return the pharmacological classes for a drug name.

    Tries exact match first, then checks if the name contains a known drug
    (handles compound names like 'Lidocaine with epinephrine').
    """
    lower = name.lower().strip()

    # Exact match
    classes = _DRUG_CLASSES.get(lower)
    if classes:
        return set(classes)

    # Partial match — check if any known drug name is contained in the input
    # This handles "Lidocaine with epinephrine", "Codeine phosphate", etc.
    found: set[str] = set()
    for known_name, known_classes in _DRUG_CLASSES.items():
        if known_name in lower or lower in known_name:
            found.update(known_classes)

    return found


def _check_class_interaction(
    classes_a: set[str], classes_b: set[str]
) -> list[tuple[str, str]]:
    """Check if two sets of drug classes have known interactions.
    Returns list of (severity, description) tuples.
    """
    results = []
    seen_descs: set[str] = set()
    for rule_a, rule_b, severity, description in _CLASS_INTERACTIONS:
        if (rule_a & classes_a and rule_b & classes_b) or \
           (rule_a & classes_b and rule_b & classes_a):
            # Deduplicate by description prefix
            key = description[:60]
            if key not in seen_descs:
                seen_descs.add(key)
                results.append((severity, description))
    return results


def get_interactions(
    current_medications: list[MedicationInput],
    candidate: MedicationInput,
) -> list[RxNavInteraction]:
    """Look up drug-drug interactions from the local curated database.

    Uses pharmacological class mapping to identify interactions.
    Returns immediately — no network calls.
    """
    candidate_classes = _get_drug_classes(candidate.name)
    if not candidate_classes:
        logger.info("No class mapping for candidate %r", candidate.name)

    interactions: list[RxNavInteraction] = []
    seen: set[str] = set()

    for med in current_medications:
        med_classes = _get_drug_classes(med.name)
        if not med_classes:
            continue

        matches = _check_class_interaction(med_classes, candidate_classes)
        for severity, description in matches:
            key = f"{med.name.lower()}|{candidate.name.lower()}|{description[:50]}"
            if key in seen:
                continue
            seen.add(key)
            interactions.append(RxNavInteraction(
                drug1=med.name,
                drug2=candidate.name,
                description=description,
                severity=severity,
                source_url=_SOURCE_URL,
            ))

    # Also check current-med vs current-med interactions
    for i, med_a in enumerate(current_medications):
        for med_b in current_medications[i + 1:]:
            classes_a = _get_drug_classes(med_a.name)
            classes_b = _get_drug_classes(med_b.name)
            if not classes_a or not classes_b:
                continue
            matches = _check_class_interaction(classes_a, classes_b)
            for severity, description in matches:
                key = f"{med_a.name.lower()}|{med_b.name.lower()}|{description[:50]}"
                if key in seen:
                    continue
                seen.add(key)
                interactions.append(RxNavInteraction(
                    drug1=med_a.name,
                    drug2=med_b.name,
                    description=description,
                    severity=severity,
                    source_url=_SOURCE_URL,
                ))

    logger.info("Local DB found %d interaction(s)", len(interactions))
    return interactions


def get_condition_interactions(
    medications: list[MedicationInput],
    conditions: list[str],
) -> list[RxNavInteraction]:
    """Look up drug-class + patient-condition interactions.

    Checks each medication's drug classes against the patient's conditions.
    Returns interactions where a drug class is dangerous given a specific condition.
    """
    if not conditions:
        return []

    condition_lower = {c.lower().strip() for c in conditions}
    interactions: list[RxNavInteraction] = []
    seen: set[str] = set()

    for med in medications:
        med_classes = _get_drug_classes(med.name)
        if not med_classes:
            continue

        for rule_classes, rule_conditions, severity, description in _CONDITION_INTERACTIONS:
            # Check if drug has a matching class AND patient has a matching condition
            if not (rule_classes & med_classes):
                continue
            if not any(
                any(kw in cond for kw in rule_conditions)
                for cond in condition_lower
            ):
                continue

            key = f"{med.name.lower()}|condition|{description[:50]}"
            if key in seen:
                continue
            seen.add(key)
            interactions.append(RxNavInteraction(
                drug1=med.name,
                drug2=f"[condition: {', '.join(c for c in conditions if any(kw in c.lower() for kw in rule_conditions))}]",
                description=description,
                severity=severity,
                source_url=_SOURCE_URL,
            ))

    logger.info("Condition DB found %d interaction(s)", len(interactions))
    return interactions


def compute_risk_amplification(
    age: int,
    conditions: list[str],
    medication_count: int,
) -> list[tuple[str, str]]:
    """Compute patient-specific risk amplification factors.

    Returns list of (factor_type, reason) tuples describing why this
    patient's risk is elevated beyond the base drug interaction severity.
    """
    factors: list[tuple[str, str]] = []
    condition_lower = {c.lower().strip() for c in conditions}

    # Age-based amplification
    if age >= 75:
        factors.append(("age", f"Patient age {age} (>75) significantly increases all "
                        "drug interaction risks due to reduced hepatic/renal clearance."))
    elif age >= 65:
        factors.append(("age", f"Patient age {age} (>65) increases risk of adverse "
                        "drug reactions, bleeding, and sedation sensitivity."))

    # Polypharmacy
    if medication_count >= 5:
        factors.append(("polypharmacy", f"Patient is on {medication_count} medications — "
                        "interaction probability increases with medication count."))

    # Condition-based amplification
    for rule_conditions, factor_type, reason in _RISK_AMPLIFIERS:
        if any(
            any(kw in cond for kw in rule_conditions)
            for cond in condition_lower
        ):
            # Avoid duplicate factor types
            if not any(f[0] == factor_type for f in factors):
                factors.append((factor_type, reason))

    return factors


def compute_minimum_risk_level(
    interactions: list[RxNavInteraction],
    amplification_factors: list[tuple[str, str]],
) -> str:
    """Compute the minimum risk level that GPT-4o cannot go below.

    Logic:
    - If any interaction is severity "high" → minimum is "high"
    - If any interaction is "medium" AND patient has amplification factors → "high"
    - If any interaction is "medium" → minimum is "medium"
    - Otherwise → "low"
    """
    if not interactions:
        return "low"

    severities = {(i.severity or "").lower() for i in interactions}
    has_amplifiers = len(amplification_factors) > 0

    if "high" in severities or "contraindicated" in severities:
        return "high"
    if "medium" in severities and has_amplifiers:
        return "high"
    if "medium" in severities:
        return "medium"
    return "low"
