"""Unit tests for backend/seed.py — {{Placeholder}} extraction and the
admin password-reset marker (the mechanism that stops demo-password sync from
overwriting passwords an admin has manually reset)."""
import pytest

from db import ConfigRecord
from seed import (
    PASSWORD_RESET_KEY,
    extract_template_variables,
    get_manual_password_resets,
    mark_password_reset,
)


@pytest.fixture(autouse=True)
def _clean_password_resets(db_session):
    """The marker record persists in the shared file DB — wipe it per test."""
    row = db_session.query(ConfigRecord).filter(ConfigRecord.key == PASSWORD_RESET_KEY).first()
    if row:
        db_session.delete(row)
        db_session.commit()
    yield
    row = db_session.query(ConfigRecord).filter(ConfigRecord.key == PASSWORD_RESET_KEY).first()
    if row:
        db_session.delete(row)
        db_session.commit()


# ---------------------------------------------------------------------------
# extract_template_variables
# ---------------------------------------------------------------------------


def test_no_placeholders_returns_empty():
    payload = {"description": "plain text, no braces", "channels": {}}
    assert extract_template_variables(payload) == []


def test_extracts_from_description():
    payload = {"description": "Hello {{Name}}, welcome.", "channels": {}}
    assert extract_template_variables(payload) == ["Name"]


def test_extracts_from_channel_subject_and_content():
    payload = {
        "description": "",
        "channels": {
            "email": {"subject": "Project {{ProjectName}}", "content": "<p>Dear {{ClientName}}, start {{ProjectName}} now.</p>"},
        },
    }
    # order of first appearance, deduped
    assert extract_template_variables(payload) == ["ProjectName", "ClientName"]


def test_extracts_from_sections():
    payload = {
        "description": "",
        "channels": {},
        "sections": [{"defaultContent": "Sign off by {{Manager}} by {{Date}}"}],
    }
    assert extract_template_variables(payload) == ["Manager", "Date"]


def test_extracts_from_checklist():
    payload = {
        "description": "",
        "channels": {},
        "checklistItems": [{"title": "Confirm {{Venue}}", "description": "Booked by {{Coordinator}}"}],
    }
    assert extract_template_variables(payload) == ["Venue", "Coordinator"]


def test_duplicates_are_deduped_preserving_first_seen_order():
    payload = {
        "description": "{{Name}} and {{Company}} then {{Name}} again",
        "channels": {},
    }
    assert extract_template_variables(payload) == ["Name", "Company"]


def test_whitespace_inside_braces_is_normalized():
    payload = {"description": "Hello {{  Client  }}!", "channels": {}}
    assert extract_template_variables(payload) == ["Client"]


def test_spaces_inside_variable_name_not_matched():
    # Variable names are single tokens (CamelCase, no internal spaces).
    payload = {"description": "{{Client Name}}", "channels": {}}
    assert extract_template_variables(payload) == []


def test_ignores_legacy_brackets_and_single_braces():
    payload = {
        "description": "[Start Date] and {single} and {{Real}}",
        "channels": {},
    }
    assert extract_template_variables(payload) == ["Real"]


# ---------------------------------------------------------------------------
# password-reset marker (protects manually-reset passwords from demo sync)
# ---------------------------------------------------------------------------


def test_mark_password_reset_is_idempotent(db_session):
    mark_password_reset(db_session, "editor@pixoustech.com")
    mark_password_reset(db_session, "editor@pixoustech.com")
    assert get_manual_password_resets(db_session) == {"editor@pixoustech.com"}


def test_get_manual_password_resets_empty_when_no_record(db_session):
    assert get_manual_password_resets(db_session) == set()


def test_mark_password_reset_multiple_emails(db_session):
    mark_password_reset(db_session, "a@pixoustech.com")
    mark_password_reset(db_session, "b@pixoustech.com")
    assert get_manual_password_resets(db_session) == {"a@pixoustech.com", "b@pixoustech.com"}


def test_password_reset_marker_persists_across_sessions():
    """Regression: the marker must survive a commit and be visible from a fresh
    session — an in-place JSON append used to be silently lost."""
    from db import SessionLocal

    s1 = SessionLocal()
    mark_password_reset(s1, "first@pixoustech.com")
    s1.close()

    s2 = SessionLocal()
    mark_password_reset(s2, "second@pixoustech.com")
    s2.close()

    s3 = SessionLocal()
    assert get_manual_password_resets(s3) == {"first@pixoustech.com", "second@pixoustech.com"}
    s3.close()
