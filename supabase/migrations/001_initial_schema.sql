-- Migration 001: Initial schema (reverse-engineered from production)
-- These tables were created manually in Supabase. This file captures
-- their exact schema for version control purposes.

CREATE TABLE IF NOT EXISTS api_keys (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash text NOT NULL,
    label text,
    revoked boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id uuid NOT NULL,
    request_hash text NOT NULL,
    risk_level text,
    latency_ms integer NOT NULL,
    fallback boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS cached_analyses (
    request_id text PRIMARY KEY,
    response jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
