"""
Tests for core/config.py — Settings startup validation.
"""
import os
from unittest.mock import patch

import pytest
from hypothesis import given, settings as h_settings
from hypothesis import strategies as st
from pydantic import ValidationError

# Feature: clarvyn-python-api, Property 21: Missing required env var prevents startup
REQUIRED_VARS = ["OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_KEY", "ADMIN_KEY"]

ALL_REQUIRED_ENV = {
    "OPENAI_API_KEY": "sk-test",
    "SUPABASE_URL": "https://test.supabase.co",
    "SUPABASE_SERVICE_KEY": "service-key",
    "ADMIN_KEY": "admin-key",
}


@given(st.sampled_from(REQUIRED_VARS))
@h_settings(max_examples=100)
def test_missing_required_env_var_raises_validation_error(missing_var: str):
    """
    # Feature: clarvyn-python-api, Property 21: Missing required env var prevents startup
    Validates: Requirements 13.2

    For each required env var, omitting it must cause Settings() to raise ValidationError.
    """
    from core.config import Settings

    env = {k: v for k, v in ALL_REQUIRED_ENV.items() if k != missing_var}

    # clear=True ensures no other env vars (or .env file values already in os.environ) leak in
    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(ValidationError):
            # Pass _env_file=None so pydantic-settings doesn't fall back to reading .env from disk
            Settings(_env_file=None)


def test_all_required_vars_present_succeeds():
    """Unit test: Settings() succeeds when all required vars are present."""
    from core.config import Settings

    with patch.dict(os.environ, ALL_REQUIRED_ENV, clear=True):
        s = Settings(_env_file=None)
        assert s.openai_api_key == "sk-test"
        assert s.supabase_url == "https://test.supabase.co"
        assert s.supabase_service_key == "service-key"
        assert s.admin_key == "admin-key"


def test_optional_fields_have_correct_defaults():
    """Unit test: Optional fields default to expected values."""
    from core.config import Settings

    with patch.dict(os.environ, ALL_REQUIRED_ENV, clear=True):
        s = Settings(_env_file=None)
        assert s.port == 8000
        assert s.pubmed_enabled is True
        assert s.log_level == "INFO"
