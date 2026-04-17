-- Migration 002: Drug knowledge base tables
-- Replaces hardcoded Python dictionaries in services/interaction_db.py
-- with queryable Supabase tables. specialty column future-proofs for
-- multi-specialty expansion beyond dentistry.

CREATE TABLE IF NOT EXISTS drug_classes (
    drug_name text PRIMARY KEY,
    classes text[] NOT NULL,
    source text NOT NULL DEFAULT 'manual',
    specialty text NOT NULL DEFAULT 'dental',
    pending_review boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS class_interactions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    classes_a text[] NOT NULL,
    classes_b text[] NOT NULL,
    severity text NOT NULL,
    description text NOT NULL,
    source text NOT NULL DEFAULT 'manual',
    specialty text NOT NULL DEFAULT 'dental',
    pending_review boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS condition_interactions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    drug_classes text[] NOT NULL,
    condition_keywords text[] NOT NULL,
    severity text NOT NULL,
    description text NOT NULL,
    source text NOT NULL DEFAULT 'manual',
    specialty text NOT NULL DEFAULT 'dental',
    pending_review boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_drug_classes_specialty
    ON drug_classes(specialty);

CREATE INDEX IF NOT EXISTS idx_class_interactions_specialty
    ON class_interactions(specialty);

CREATE INDEX IF NOT EXISTS idx_condition_interactions_specialty
    ON condition_interactions(specialty);
