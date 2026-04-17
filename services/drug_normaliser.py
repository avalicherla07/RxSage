"""Drug name normalisation for consistent lookup."""
from __future__ import annotations
import re

BRAND_TO_GENERIC: dict[str, str] = {
    "tylenol": "acetaminophen", "advil": "ibuprofen", "motrin": "ibuprofen",
    "aleve": "naproxen", "coumadin": "warfarin", "xarelto": "rivaroxaban",
    "eliquis": "apixaban", "plavix": "clopidogrel", "zithromax": "azithromycin",
    "biaxin": "clarithromycin", "flagyl": "metronidazole", "diflucan": "fluconazole",
    "valium": "diazepam", "xanax": "alprazolam", "ativan": "lorazepam",
    "halcion": "triazolam", "vistaril": "hydroxyzine",
    "augmentin": "amoxicillin-clavulanate", "zocor": "simvastatin",
    "lipitor": "atorvastatin", "crestor": "rosuvastatin", "glucophage": "metformin",
    "synthroid": "levothyroxine", "prilosec": "omeprazole", "nexium": "esomeprazole",
    "pepcid": "famotidine", "tagamet": "cimetidine", "lasix": "furosemide",
    "lopressor": "metoprolol", "toprol": "metoprolol", "coreg": "carvedilol",
    "norvasc": "amlodipine", "prozac": "fluoxetine", "zoloft": "sertraline",
    "lexapro": "escitalopram", "effexor": "venlafaxine", "wellbutrin": "bupropion",
    "abilify": "aripiprazole", "seroquel": "quetiapine", "risperdal": "risperidone",
    "fosamax": "alendronate", "boniva": "ibandronate", "reclast": "zoledronic acid",
    "medrol": "methylprednisolone", "deltasone": "prednisone",
    "adderall": "amphetamine salts", "ritalin": "methylphenidate",
    "concerta": "methylphenidate",
}

def normalise_drug_name(raw_name: str) -> str:
    if not raw_name:
        return raw_name
    name = raw_name.lower().strip()
    name = re.sub(r'\([^)]*\)', '', name).strip()
    name = re.sub(
        r'\b\d+\.?\d*\s*(mg|mcg|ug|g|ml|l|iu|units?|mmol|meq|%)\b',
        '', name, flags=re.IGNORECASE).strip()
    name = re.sub(
        r'\b(tid|bid|qid|qd|prn|daily|once|twice|weekly|monthly|as needed|'
        r'tablet|capsule|solution|suspension|injection|cream|ointment|patch|'
        r'oral|topical|extended.release|immediate.release|er|sr|cr|xl|xr)\b',
        '', name, flags=re.IGNORECASE).strip()
    name = re.sub(r'\s+', ' ', name).strip().strip('/-').strip()
    if name in BRAND_TO_GENERIC:
        return BRAND_TO_GENERIC[name]
    first = name.split()[0] if name.split() else name
    if first in BRAND_TO_GENERIC:
        return BRAND_TO_GENERIC[first]
    return name.strip()
