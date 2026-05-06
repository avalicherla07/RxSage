-- Migration 003: Seed dental drug knowledge base
-- Populates drug_classes, class_interactions, and condition_interactions
-- with curated data from services/interaction_db.py.
-- Safe to re-run: all INSERTs use ON CONFLICT DO NOTHING.

BEGIN;

-- ═══════════════════════════════════════════════════════════════════════════
-- drug_classes — one row per drug
-- ═══════════════════════════════════════════════════════════════════════════

-- Anticoagulants / Antithrombotics
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('warfarin', ARRAY['anticoagulant','vitamin_k_antagonist'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('heparin', ARRAY['anticoagulant'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('enoxaparin', ARRAY['anticoagulant','lmwh'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('rivaroxaban', ARRAY['anticoagulant','doac'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('apixaban', ARRAY['anticoagulant','doac','cyp3a4_substrate'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('dabigatran', ARRAY['anticoagulant','doac'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('edoxaban', ARRAY['anticoagulant','doac'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('clopidogrel', ARRAY['antiplatelet'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('prasugrel', ARRAY['antiplatelet'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('ticagrelor', ARRAY['antiplatelet'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('aspirin', ARRAY['nsaid','antiplatelet'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('dipyridamole', ARRAY['antiplatelet'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- NSAIDs
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('ibuprofen', ARRAY['nsaid'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('naproxen', ARRAY['nsaid'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('diclofenac', ARRAY['nsaid'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('celecoxib', ARRAY['nsaid','cox2_inhibitor'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('meloxicam', ARRAY['nsaid'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('ketorolac', ARRAY['nsaid'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('indomethacin', ARRAY['nsaid'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('piroxicam', ARRAY['nsaid'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('mefenamic acid', ARRAY['nsaid'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Antibiotics
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('amoxicillin', ARRAY['antibiotic','penicillin'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('ampicillin', ARRAY['antibiotic','penicillin'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('penicillin', ARRAY['antibiotic','penicillin'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('clindamycin', ARRAY['antibiotic','lincosamide'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('metronidazole', ARRAY['antibiotic','nitroimidazole','cyp2c9_inhibitor'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('azithromycin', ARRAY['antibiotic','macrolide'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('erythromycin', ARRAY['antibiotic','macrolide','cyp3a4_inhibitor','qt_prolonging'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('clarithromycin', ARRAY['antibiotic','macrolide','cyp3a4_inhibitor','qt_prolonging'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('ciprofloxacin', ARRAY['antibiotic','fluoroquinolone','cyp1a2_inhibitor'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('levofloxacin', ARRAY['antibiotic','fluoroquinolone','qt_prolonging'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('moxifloxacin', ARRAY['antibiotic','fluoroquinolone','qt_prolonging'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('doxycycline', ARRAY['antibiotic','tetracycline'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('tetracycline', ARRAY['antibiotic','tetracycline'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('minocycline', ARRAY['antibiotic','tetracycline'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('trimethoprim', ARRAY['antibiotic'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('sulfamethoxazole', ARRAY['antibiotic'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Antifungals
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('fluconazole', ARRAY['antifungal','cyp2c9_inhibitor','cyp3a4_inhibitor'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('itraconazole', ARRAY['antifungal','cyp3a4_inhibitor'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('ketoconazole', ARRAY['antifungal','cyp3a4_inhibitor'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('nystatin', ARRAY['antifungal'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('clotrimazole', ARRAY['antifungal'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Antihypertensives
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('lisinopril', ARRAY['ace_inhibitor','antihypertensive'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('enalapril', ARRAY['ace_inhibitor','antihypertensive'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('ramipril', ARRAY['ace_inhibitor','antihypertensive'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('losartan', ARRAY['arb','antihypertensive'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('valsartan', ARRAY['arb','antihypertensive'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('irbesartan', ARRAY['arb','antihypertensive'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('amlodipine', ARRAY['ccb','antihypertensive'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('nifedipine', ARRAY['ccb','antihypertensive'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('diltiazem', ARRAY['ccb','antihypertensive','cyp3a4_inhibitor'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('verapamil', ARRAY['ccb','antihypertensive','cyp3a4_inhibitor'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('metoprolol', ARRAY['beta_blocker','antihypertensive'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('atenolol', ARRAY['beta_blocker','antihypertensive'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('propranolol', ARRAY['beta_blocker','antihypertensive','nonselective_beta_blocker'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('carvedilol', ARRAY['beta_blocker','antihypertensive','nonselective_beta_blocker'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('nadolol', ARRAY['beta_blocker','antihypertensive','nonselective_beta_blocker'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('labetalol', ARRAY['beta_blocker','antihypertensive','nonselective_beta_blocker'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('furosemide', ARRAY['diuretic','loop_diuretic'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('hydrochlorothiazide', ARRAY['diuretic','thiazide'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('spironolactone', ARRAY['diuretic','potassium_sparing'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Cardiac glycosides
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('digoxin', ARRAY['cardiac_glycoside','arrhythmia_sensitive'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Diabetes
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('metformin', ARRAY['antidiabetic','biguanide'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('glipizide', ARRAY['antidiabetic','sulfonylurea'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('glyburide', ARRAY['antidiabetic','sulfonylurea'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('glimepiride', ARRAY['antidiabetic','sulfonylurea'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('insulin', ARRAY['antidiabetic','insulin'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('sitagliptin', ARRAY['antidiabetic'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('empagliflozin', ARRAY['antidiabetic','sglt2_inhibitor'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- SSRIs / SNRIs / Antidepressants
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('sertraline', ARRAY['ssri','antidepressant','serotonergic'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('fluoxetine', ARRAY['ssri','antidepressant','cyp2d6_inhibitor','serotonergic'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('paroxetine', ARRAY['ssri','antidepressant','cyp2d6_inhibitor','serotonergic'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('citalopram', ARRAY['ssri','antidepressant','serotonergic','qt_prolonging'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('escitalopram', ARRAY['ssri','antidepressant','serotonergic','qt_prolonging'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('venlafaxine', ARRAY['snri','antidepressant','serotonergic'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('duloxetine', ARRAY['snri','antidepressant','serotonergic'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Tricyclic antidepressants
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('amitriptyline', ARRAY['tca','antidepressant','norepinephrine_reuptake_inhibitor','qt_prolonging'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('nortriptyline', ARRAY['tca','antidepressant','norepinephrine_reuptake_inhibitor'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('imipramine', ARRAY['tca','antidepressant','norepinephrine_reuptake_inhibitor','qt_prolonging'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('desipramine', ARRAY['tca','antidepressant','norepinephrine_reuptake_inhibitor'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('doxepin', ARRAY['tca','antidepressant','norepinephrine_reuptake_inhibitor'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- MAOIs
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('phenelzine', ARRAY['maoi','antidepressant'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('tranylcypromine', ARRAY['maoi','antidepressant'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('selegiline', ARRAY['maoi'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Antipsychotics
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('haloperidol', ARRAY['antipsychotic','qt_prolonging'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('chlorpromazine', ARRAY['antipsychotic','qt_prolonging'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('quetiapine', ARRAY['antipsychotic','qt_prolonging'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('risperidone', ARRAY['antipsychotic'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('olanzapine', ARRAY['antipsychotic'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('aripiprazole', ARRAY['antipsychotic'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('ziprasidone', ARRAY['antipsychotic','qt_prolonging'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Benzodiazepines / Sedatives
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('diazepam', ARRAY['benzodiazepine','sedative','cns_depressant'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('midazolam', ARRAY['benzodiazepine','sedative','cns_depressant','cyp3a4_substrate'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('triazolam', ARRAY['benzodiazepine','sedative','cns_depressant','cyp3a4_substrate'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('lorazepam', ARRAY['benzodiazepine','sedative','cns_depressant'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('alprazolam', ARRAY['benzodiazepine','sedative','cns_depressant','cyp3a4_substrate'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('zolpidem', ARRAY['sedative','cns_depressant'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('zopiclone', ARRAY['sedative','cns_depressant'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Opioids
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('codeine', ARRAY['opioid','analgesic','cns_depressant','cyp2d6_substrate'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('codeine phosphate', ARRAY['opioid','analgesic','cns_depressant','cyp2d6_substrate'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('hydrocodone', ARRAY['opioid','analgesic','cns_depressant'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('oxycodone', ARRAY['opioid','analgesic','cns_depressant'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('tramadol', ARRAY['opioid','analgesic','cns_depressant','serotonergic'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('fentanyl', ARRAY['opioid','analgesic','cns_depressant'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('morphine', ARRAY['opioid','analgesic','cns_depressant'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('meperidine', ARRAY['opioid','analgesic','cns_depressant','serotonergic'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Corticosteroids
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('prednisone', ARRAY['corticosteroid'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('prednisolone', ARRAY['corticosteroid'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('dexamethasone', ARRAY['corticosteroid'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('hydrocortisone', ARRAY['corticosteroid'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('methylprednisolone', ARRAY['corticosteroid'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Statins
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('atorvastatin', ARRAY['statin','cyp3a4_substrate'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('simvastatin', ARRAY['statin','cyp3a4_substrate'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('rosuvastatin', ARRAY['statin'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('lovastatin', ARRAY['statin','cyp3a4_substrate'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('pravastatin', ARRAY['statin'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- PPIs / H2 blockers
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('omeprazole', ARRAY['ppi','cyp2c19_inhibitor'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('pantoprazole', ARRAY['ppi'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('esomeprazole', ARRAY['ppi','cyp2c19_inhibitor'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('lansoprazole', ARRAY['ppi'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('cimetidine', ARRAY['h2_blocker','cyp_inhibitor_broad'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('ranitidine', ARRAY['h2_blocker'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('famotidine', ARRAY['h2_blocker'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Local anesthetics (dental)
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('lidocaine', ARRAY['local_anesthetic','cyp_hepatic_substrate'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('lidocaine with epinephrine', ARRAY['local_anesthetic','cyp_hepatic_substrate','vasoconstrictor','sympathomimetic'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('articaine', ARRAY['local_anesthetic'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('bupivacaine', ARRAY['local_anesthetic'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('mepivacaine', ARRAY['local_anesthetic'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('prilocaine', ARRAY['local_anesthetic'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Vasoconstrictors (dental)
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('epinephrine', ARRAY['vasoconstrictor','sympathomimetic'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Lithium
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('lithium', ARRAY['lithium','narrow_therapeutic_index'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('lithium carbonate', ARRAY['lithium','narrow_therapeutic_index'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Methotrexate
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('methotrexate', ARRAY['methotrexate','immunosuppressant','narrow_therapeutic_index'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Bisphosphonates
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('alendronate', ARRAY['bisphosphonate','bone_resorption_inhibitor'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('risedronate', ARRAY['bisphosphonate','bone_resorption_inhibitor'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('zoledronic acid', ARRAY['bisphosphonate','bone_resorption_inhibitor','iv_bisphosphonate'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('ibandronate', ARRAY['bisphosphonate','bone_resorption_inhibitor'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('denosumab', ARRAY['bone_resorption_inhibitor'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Immunosuppressants
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('tacrolimus', ARRAY['immunosuppressant','calcineurin_inhibitor','narrow_therapeutic_index'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('cyclosporine', ARRAY['immunosuppressant','calcineurin_inhibitor','narrow_therapeutic_index'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('mycophenolate mofetil', ARRAY['immunosuppressant'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('mycophenolate', ARRAY['immunosuppressant'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('azathioprine', ARRAY['immunosuppressant'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('sirolimus', ARRAY['immunosuppressant'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Anticonvulsants
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('phenytoin', ARRAY['anticonvulsant','narrow_therapeutic_index','cyp_inducer'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('carbamazepine', ARRAY['anticonvulsant','cyp_inducer','cyp3a4_inducer'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('valproic acid', ARRAY['anticonvulsant'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('gabapentin', ARRAY['anticonvulsant'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('pregabalin', ARRAY['anticonvulsant'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('lamotrigine', ARRAY['anticonvulsant'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('levetiracetam', ARRAY['anticonvulsant'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Dental procedures (special entries)
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('tooth extraction procedure', ARRAY['invasive_dental_procedure'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('dental implant procedure', ARRAY['invasive_dental_procedure','bone_dependent_procedure'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;
INSERT INTO drug_classes (drug_name, classes, source, specialty, pending_review) VALUES
  ('dental surgery', ARRAY['invasive_dental_procedure'], 'manual', 'dental', false)
  ON CONFLICT DO NOTHING;


-- ═══════════════════════════════════════════════════════════════════════════
-- class_interactions — one row per interaction rule
-- ═══════════════════════════════════════════════════════════════════════════

-- Anticoagulant interactions
INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['anticoagulant'], ARRAY['nsaid'], 'high',
   'NSAIDs may significantly increase bleeding risk when combined with anticoagulants. NSAIDs inhibit platelet function and may cause GI bleeding. This combination could lead to serious or life-threatening hemorrhage. Consider acetaminophen as an alternative.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['anticoagulant'], ARRAY['antiplatelet'], 'high',
   'Combining anticoagulants with antiplatelet agents significantly increases bleeding risk. Monitor for signs of bleeding during and after dental procedures.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['vitamin_k_antagonist'], ARRAY['nitroimidazole'], 'high',
   'Metronidazole inhibits CYP2C9, the primary enzyme that metabolises warfarin. INR can double or triple within days, causing potentially fatal bleeding. Monitor INR closely or consider alternative antibiotics.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['vitamin_k_antagonist'], ARRAY['cyp2c9_inhibitor'], 'high',
   'CYP2C9 inhibitors (fluconazole, metronidazole) may significantly increase warfarin levels by blocking its primary metabolic pathway. INR may rise dangerously. Monitor INR closely and consider dose reduction.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['vitamin_k_antagonist'], ARRAY['macrolide'], 'high',
   'Macrolide antibiotics (erythromycin, clarithromycin) may increase warfarin levels by inhibiting CYP3A4 metabolism, potentially leading to elevated INR and bleeding risk. Consider azithromycin (lower interaction potential) or monitor INR closely.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['vitamin_k_antagonist'], ARRAY['fluoroquinolone'], 'medium',
   'Fluoroquinolones may enhance the anticoagulant effect of warfarin. Monitor INR if ciprofloxacin or similar agents are prescribed concurrently.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- NSAID interactions
INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['nsaid'], ARRAY['ace_inhibitor'], 'medium',
   'NSAIDs may reduce the antihypertensive effect of ACE inhibitors and increase the risk of renal impairment. Blood pressure monitoring may be warranted.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['nsaid'], ARRAY['arb'], 'medium',
   'NSAIDs may reduce the antihypertensive effect of ARBs and increase the risk of renal impairment, particularly in patients with existing renal compromise.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['nsaid'], ARRAY['ssri'], 'medium',
   'SSRIs deplete platelet serotonin, impairing aggregation. Combined with NSAIDs, there is a significantly elevated risk of GI bleeding. Consider gastroprotective therapy or acetaminophen as an alternative analgesic.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['nsaid'], ARRAY['snri'], 'medium',
   'SNRIs may impair platelet function similarly to SSRIs. Combined with NSAIDs, bleeding risk may be elevated. Consider gastroprotective measures.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['nsaid'], ARRAY['corticosteroid'], 'medium',
   'Concurrent use of NSAIDs and corticosteroids may increase the risk of GI ulceration and bleeding. Consider gastroprotective measures.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['nsaid'], ARRAY['lithium'], 'high',
   'NSAIDs inhibit renal prostaglandins, reducing lithium excretion. Lithium has a narrow therapeutic index — levels can rise rapidly to toxic concentrations. This combination may cause serious lithium toxicity. Consider acetaminophen instead.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['nsaid'], ARRAY['methotrexate'], 'high',
   'NSAIDs reduce renal clearance of methotrexate, potentially causing life-threatening toxicity including bone marrow suppression and renal failure. Avoid this combination especially with high-dose methotrexate. Consider acetaminophen.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['nsaid'], ARRAY['diuretic'], 'medium',
   'NSAIDs may reduce the effectiveness of diuretics and increase the risk of renal impairment, particularly in elderly patients or those with heart failure.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Opioid / CNS depressant interactions
INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['opioid'], ARRAY['benzodiazepine'], 'high',
   'Concurrent use of opioids and benzodiazepines may result in profound sedation, respiratory depression, coma, or death. FDA black box warning. Use the lowest effective doses and shortest duration if combination is necessary.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['opioid'], ARRAY['sedative'], 'high',
   'Combining opioids with sedative-hypnotics (including zolpidem) increases the risk of profound CNS depression and respiratory failure. Avoid if possible.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['opioid'], ARRAY['serotonergic'], 'medium',
   'Combining opioids (especially tramadol, meperidine) with serotonergic drugs (SSRIs, SNRIs) may increase the risk of serotonin syndrome. Monitor for agitation, confusion, rapid heart rate, and muscle rigidity.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['cyp2d6_substrate'], ARRAY['cyp2d6_inhibitor'], 'medium',
   'CYP2D6 inhibitors (fluoxetine, paroxetine) block the conversion of codeine to morphine, making codeine ineffective for pain relief. Toxic codeine metabolites may also accumulate. Consider alternative analgesics.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['opioid'], ARRAY['maoi'], 'high',
   'Combining opioids with MAOIs can cause serotonin syndrome, severe respiratory depression, or hypertensive crisis. This combination is contraindicated. Wait at least 14 days after stopping an MAOI before prescribing opioids.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Local anesthetic / vasoconstrictor interactions
INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['local_anesthetic'], ARRAY['beta_blocker'], 'medium',
   'Beta-blockers may reduce hepatic metabolism of local anesthetics (especially lidocaine), potentially increasing plasma levels and risk of toxicity. Use lower doses.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['sympathomimetic'], ARRAY['nonselective_beta_blocker'], 'high',
   'Epinephrine in dental anesthetics combined with non-selective beta-blockers (propranolol, carvedilol, nadolol) may cause acute hypertensive crisis and reflex bradycardia. Beta-2 vasodilation is blocked, leaving alpha-1 vasoconstriction unopposed. Use minimal epinephrine or consider mepivacaine without vasoconstrictor.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['sympathomimetic'], ARRAY['beta_blocker'], 'medium',
   'Epinephrine in dental anesthetics may interact with beta-blockers. While selective beta-blockers (metoprolol, atenolol) carry lower risk than non-selective agents, blood pressure monitoring is still recommended. Use minimal epinephrine and aspirate.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['sympathomimetic'], ARRAY['tca'], 'high',
   'Tricyclic antidepressants block norepinephrine reuptake — epinephrine accumulates at adrenergic receptors, amplifying cardiovascular effects 2-3x. Risk of severe hypertension and cardiac arrhythmias. Use minimal epinephrine with aspiration.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['sympathomimetic'], ARRAY['maoi'], 'high',
   'MAOIs prevent breakdown of catecholamines. Epinephrine in dental anesthetics may cause severe hypertensive crisis. Avoid epinephrine-containing anesthetics entirely.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['sympathomimetic'], ARRAY['cardiac_glycoside'], 'high',
   'Digoxin sensitises the myocardium to catecholamines. Combined with epinephrine, this may trigger serious cardiac arrhythmias including ventricular fibrillation. Use minimal epinephrine concentration and monitor cardiac rhythm.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['cyp_hepatic_substrate'], ARRAY['cyp_inhibitor_broad'], 'high',
   'Cimetidine broadly inhibits hepatic CYP enzymes required to metabolise lidocaine, raising plasma lidocaine levels and increasing risk of CNS toxicity (tinnitus, perioral numbness, seizures). Use lowest effective lidocaine dose.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- CYP3A4 interactions
INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['cyp3a4_inhibitor'], ARRAY['cyp3a4_substrate'], 'high',
   'CYP3A4 inhibitors (erythromycin, clarithromycin, fluconazole, itraconazole, diltiazem, verapamil) may significantly increase plasma levels of CYP3A4 substrates (midazolam, triazolam, alprazolam, simvastatin, atorvastatin), leading to excessive sedation or rhabdomyolysis. Consider alternative agents.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['cyp3a4_inhibitor'], ARRAY['statin'], 'high',
   'CYP3A4 inhibitors may dramatically increase statin levels, raising the risk of rhabdomyolysis. Most relevant for simvastatin and lovastatin. Consider rosuvastatin or pravastatin as alternatives (not CYP3A4 dependent).',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- QT prolongation
INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['qt_prolonging'], ARRAY['qt_prolonging'], 'high',
   'Combining two QT-prolonging drugs significantly increases the risk of fatal cardiac arrhythmias (Torsades de Pointes). Macrolide antibiotics + antipsychotics, or macrolides + certain SSRIs, are particularly dangerous combinations. Consider alternative antibiotics (amoxicillin, clindamycin) that do not prolong QT.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Bisphosphonate / bone interactions
INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['bisphosphonate'], ARRAY['invasive_dental_procedure'], 'high',
   'Bisphosphonates (alendronate, risedronate, zoledronic acid) may cause medication-related osteonecrosis of the jaw (MRONJ) after invasive dental procedures including extractions, implant placement, and periodontal surgery. Risk is highest with IV bisphosphonates and long-duration oral therapy (>3 years). Consult prescribing physician before proceeding.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['bone_resorption_inhibitor'], ARRAY['invasive_dental_procedure'], 'high',
   'Bone resorption inhibitors (bisphosphonates, denosumab) increase the risk of osteonecrosis of the jaw (MRONJ) after invasive dental procedures. Consider drug holiday consultation with prescribing physician.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['ppi'], ARRAY['bone_dependent_procedure'], 'medium',
   'Long-term PPI use reduces calcium absorption and may decrease bone density. Studies show significantly higher dental implant failure rates in PPI users. Consider bone density assessment before implant placement.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Immunosuppressant interactions
INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['immunosuppressant'], ARRAY['antibiotic'], 'medium',
   'Immunosuppressed patients (transplant recipients on tacrolimus, cyclosporine) may have altered drug metabolism and increased infection risk. Dental infections can become life-threatening. Coordinate antibiotic selection with transplant team. Macrolide antibiotics may increase tacrolimus/cyclosporine levels via CYP3A4 inhibition.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['calcineurin_inhibitor'], ARRAY['cyp3a4_inhibitor'], 'high',
   'CYP3A4 inhibitors (erythromycin, clarithromycin, fluconazole) may dramatically increase tacrolimus or cyclosporine levels, causing nephrotoxicity and neurotoxicity. Use azithromycin or clindamycin instead.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['calcineurin_inhibitor'], ARRAY['nsaid'], 'high',
   'NSAIDs may significantly increase the nephrotoxic effects of calcineurin inhibitors (tacrolimus, cyclosporine). Avoid NSAIDs in transplant patients. Use acetaminophen.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- PPI / H2 blocker interactions
INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['ppi'], ARRAY['antiplatelet'], 'medium',
   'PPIs (especially omeprazole, esomeprazole) may reduce the antiplatelet effect of clopidogrel by inhibiting CYP2C19 activation. Consider pantoprazole as an alternative.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['cyp_inhibitor_broad'], ARRAY['local_anesthetic'], 'high',
   'Cimetidine inhibits multiple hepatic CYP enzymes, reducing lidocaine clearance and raising plasma levels. Risk of lidocaine toxicity (tinnitus, perioral numbness, seizures, cardiac arrest). Use lowest effective dose and avoid repeat cartridges.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Anticonvulsant interactions
INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['cyp_inducer'], ARRAY['anticoagulant'], 'medium',
   'CYP enzyme inducers (phenytoin, carbamazepine) may reduce warfarin levels, decreasing anticoagulant effect. INR monitoring is recommended.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['anticonvulsant'], ARRAY['opioid'], 'medium',
   'Some anticonvulsants may alter opioid metabolism. Gabapentin and pregabalin combined with opioids increase CNS depression risk.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Tetracycline interactions
INSERT INTO class_interactions (classes_a, classes_b, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['tetracycline'], ARRAY['antidiabetic'], 'low',
   'Tetracyclines may rarely enhance the hypoglycemic effect of antidiabetic agents. Monitor blood glucose if prescribing doxycycline to diabetic patients.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;


-- ═══════════════════════════════════════════════════════════════════════════
-- condition_interactions — one row per condition interaction rule
-- ═══════════════════════════════════════════════════════════════════════════

-- Immunosuppression + infection
INSERT INTO condition_interactions (drug_classes, condition_keywords, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['immunosuppressant','calcineurin_inhibitor'],
   ARRAY['transplant','immunosuppressed','immunocompromised'],
   'high',
   'Immunosuppressed patients (transplant recipients on tacrolimus, cyclosporine, mycophenolate) are at high risk for life-threatening dental infections. Dental abscesses can progress to sepsis rapidly. Coordinate antibiotic selection with transplant team. Macrolide antibiotics may increase calcineurin inhibitor levels.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO condition_interactions (drug_classes, condition_keywords, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['immunosuppressant'],
   ARRAY['dental abscess','dental infection','periapical abscess','cellulitis'],
   'high',
   'Active dental infection in an immunosuppressed patient requires urgent treatment. Risk of systemic spread is significantly elevated. Consider IV antibiotics and physician consultation before invasive dental procedures.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO condition_interactions (drug_classes, condition_keywords, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['calcineurin_inhibitor'],
   ARRAY['gingival','periodontal'],
   'medium',
   'Calcineurin inhibitors (tacrolimus, cyclosporine) commonly cause gingival overgrowth. This may complicate periodontal treatment and require medication adjustment in coordination with the prescribing physician.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Anticoagulants + bleeding-prone conditions
INSERT INTO condition_interactions (drug_classes, condition_keywords, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['anticoagulant'],
   ARRAY['liver disease','hepatic impairment','cirrhosis','coagulopathy'],
   'high',
   'Anticoagulants in patients with liver disease carry extremely high bleeding risk due to impaired clotting factor synthesis. INR may be unreliable. Consult hematology before any invasive dental procedure.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO condition_interactions (drug_classes, condition_keywords, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['anticoagulant'],
   ARRAY['renal impairment','kidney disease','ckd','dialysis'],
   'high',
   'Renal impairment affects anticoagulant clearance and platelet function. Bleeding risk is significantly elevated. Dose adjustment and close monitoring required.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- NSAIDs + renal/GI conditions
INSERT INTO condition_interactions (drug_classes, condition_keywords, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['nsaid'],
   ARRAY['renal impairment','kidney disease','ckd','dialysis'],
   'high',
   'NSAIDs are contraindicated in significant renal impairment — they reduce renal blood flow via prostaglandin inhibition, potentially causing acute kidney injury. Use acetaminophen instead.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO condition_interactions (drug_classes, condition_keywords, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['nsaid'],
   ARRAY['gi bleed','peptic ulcer','gastric ulcer','gi bleeding history'],
   'high',
   'NSAIDs in patients with GI bleeding history carry high risk of recurrent hemorrhage. Avoid NSAIDs entirely. Use acetaminophen for pain management.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Bisphosphonates + bone conditions
INSERT INTO condition_interactions (drug_classes, condition_keywords, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['bisphosphonate','bone_resorption_inhibitor'],
   ARRAY['osteoporosis','bone metastasis','paget','myeloma'],
   'medium',
   'Long-term bisphosphonate use (>3 years oral, any duration IV) increases MRONJ risk with invasive dental procedures. Risk is higher with IV bisphosphonates and concurrent corticosteroid use. Consult prescribing physician about drug holiday.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Corticosteroids + adrenal suppression
INSERT INTO condition_interactions (drug_classes, condition_keywords, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['corticosteroid'],
   ARRAY['adrenal insufficiency','addison','long-term steroid','steroid dependent'],
   'high',
   'Patients on long-term corticosteroids may have adrenal suppression. Stressful dental procedures may require supplemental corticosteroid dosing to prevent adrenal crisis. Consult prescribing physician for stress-dose protocol.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO condition_interactions (drug_classes, condition_keywords, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['corticosteroid'],
   ARRAY['diabetes','diabetic'],
   'medium',
   'Corticosteroids elevate blood glucose. Diabetic patients on corticosteroids may need glucose monitoring during and after dental procedures, especially with sedation.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Sedation risks in elderly/respiratory
INSERT INTO condition_interactions (drug_classes, condition_keywords, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['opioid','benzodiazepine','cns_depressant'],
   ARRAY['copd','sleep apnea','respiratory disease','asthma'],
   'high',
   'CNS depressants (opioids, benzodiazepines) in patients with respiratory disease carry high risk of respiratory depression. Use minimal sedation, avoid opioids if possible, and monitor oxygen saturation.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO condition_interactions (drug_classes, condition_keywords, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['opioid','benzodiazepine','cns_depressant'],
   ARRAY['elderly','frail','fall risk'],
   'high',
   'Elderly or frail patients are at increased risk of excessive sedation, falls, and respiratory depression with CNS depressants. Use lowest effective doses.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Anticonvulsants + dental
INSERT INTO condition_interactions (drug_classes, condition_keywords, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['anticonvulsant'],
   ARRAY['epilepsy','seizure disorder'],
   'medium',
   'Dental procedures may trigger seizures in epileptic patients, especially with stress or missed medication doses. Ensure patient has taken anticonvulsant medication. Have seizure management protocol ready.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

INSERT INTO condition_interactions (drug_classes, condition_keywords, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['anticonvulsant'],
   ARRAY['gingival hyperplasia','gingival overgrowth'],
   'medium',
   'Phenytoin and some other anticonvulsants cause gingival hyperplasia. Meticulous oral hygiene and regular periodontal care are essential. Consider discussing medication alternatives with neurologist.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Diabetes + infection risk
INSERT INTO condition_interactions (drug_classes, condition_keywords, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['antidiabetic'],
   ARRAY['uncontrolled diabetes','hba1c elevated','poorly controlled diabetes'],
   'medium',
   'Poorly controlled diabetes increases infection risk and impairs wound healing after dental procedures. Consider delaying elective procedures until glycemic control improves. Prophylactic antibiotics may be warranted.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

-- Cardiac conditions + epinephrine
INSERT INTO condition_interactions (drug_classes, condition_keywords, severity, description, source, specialty, pending_review) VALUES
  (ARRAY['vasoconstrictor','sympathomimetic'],
   ARRAY['arrhythmia','atrial fibrillation','ventricular tachycardia','heart failure'],
   'high',
   'Epinephrine in dental anesthetics may exacerbate cardiac arrhythmias in patients with pre-existing cardiac conditions. Use minimal epinephrine concentration, aspirate before injection, and limit to 2 cartridges maximum.',
   'manual', 'dental', false)
  ON CONFLICT DO NOTHING;

COMMIT;
