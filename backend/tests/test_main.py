"""Unit tests for backend/main.py — request-model validation (Pydantic), the
AI provider key parser and action registry, and the login rate limiter."""
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

import main as app_module
from main import (
    AI_ACTION_INSTRUCTIONS,
    ChannelData,
    TemplateBase,
    _check_login_rate_limit,
    _key_list,
)


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    app_module._LOGIN_ATTEMPTS.clear()
    yield
    app_module._LOGIN_ATTEMPTS.clear()


def valid_template(name="Unit Template"):
    return {
        "name": name,
        "description": "d",
        "purpose": "p",
        "department": "HR",
        "category": "Test Category",
        "status": "Draft",
        "owner": "Tester",
        "language": "English",
        "visibility": "Internal",
        "tags": [],
        "branding": {"logoEnabled": False, "signatureEnabled": False,
                     "footerEnabled": False, "letterheadEnabled": False,
                     "companyDetailsEnabled": False},
        "channels": {"email": {"enabled": True, "subject": "Hi {{Name}}",
                               "content": "<p>Hello {{Name}}</p>"}},
        "allowed_attachments": [],
        "sections": [],
        "checklistItems": [],
        "signoffRole": "",
        "publishing": {"priority": "Medium", "publishImmediately": False,
                       "effectiveDate": "", "expiryDate": "",
                       "audience": {"allEmployees": True, "departments": [],
                                    "locations": [], "roles": []},
                       "notificationBehavior": {"requireAcknowledgement": False,
                                                "allowComments": False}},
        "eventTrigger": {"enabled": False, "eventType": "", "autoGenerate": False,
                         "autoPublish": False, "leadTimeDays": 0},
        "banner": "",
        "variables": [],
        "approval_required": False,
        "approved_by": "",
        "created_at": "",
        "updated_at": "",
    }


# ---------------------------------------------------------------------------
# TemplateBase validation
# ---------------------------------------------------------------------------


def test_valid_template_passes():
    t = TemplateBase(**valid_template())
    assert t.name == "Unit Template"


def test_name_trims_surrounding_whitespace():
    t = TemplateBase(**valid_template("  Trim Me  "))
    assert t.name == "Trim Me"


@pytest.mark.parametrize("bad_name", ["", "   ", "\t\n"])
def test_blank_name_rejected(bad_name):
    with pytest.raises(ValidationError):
        TemplateBase(**valid_template(bad_name))


def test_one_char_name_accepted():
    assert TemplateBase(**valid_template("A")).name == "A"


def test_200_char_name_accepted():
    assert TemplateBase(**valid_template("x" * 200)).name == "x" * 200


def test_201_char_name_rejected():
    with pytest.raises(ValidationError):
        TemplateBase(**valid_template("x" * 201))


def test_10000_char_name_rejected():
    with pytest.raises(ValidationError):
        TemplateBase(**valid_template("x" * 10_000))


def test_missing_branding_rejected():
    data = valid_template()
    del data["branding"]
    with pytest.raises(ValidationError):
        TemplateBase(**data)


def test_channel_subject_max_500():
    with pytest.raises(ValidationError):
        ChannelData(enabled=True, subject="s" * 501, content="ok")


def test_channel_content_max_100000():
    with pytest.raises(ValidationError):
        ChannelData(enabled=True, subject="ok", content="c" * 100_001)


def test_channel_content_100000_accepted():
    c = ChannelData(enabled=True, subject="ok", content="c" * 100_000)
    assert len(c.content) == 100_000


# ---------------------------------------------------------------------------
# AI: key-list parsing + action registry
# ---------------------------------------------------------------------------


def test_key_list_splits_and_strips():
    assert _key_list("a, b ,,c") == ["a", "b", "c"]


def test_key_list_empty_inputs():
    assert _key_list("") == []
    assert _key_list("   ,  , ") == []


def test_ai_actions_all_have_instructions():
    expected = {"Improve", "Professional", "Friendly", "Formal", "Shorter",
                "Longer", "Grammar", "Company Tone", "Translate"}
    assert set(AI_ACTION_INSTRUCTIONS) | {"Translate"} == expected


def test_ai_action_instructions_nonempty():
    assert all(v.strip() for v in AI_ACTION_INSTRUCTIONS.values())


# ---------------------------------------------------------------------------
# Login rate limiting
# ---------------------------------------------------------------------------


def test_rate_limiter_allows_10_then_blocks():
    for _ in range(10):
        _check_login_rate_limit("1.2.3.4")   # no exception
    with pytest.raises(HTTPException) as e:
        _check_login_rate_limit("1.2.3.4")
    assert e.value.status_code == 429


def test_rate_limiter_per_ip():
    for _ in range(10):
        _check_login_rate_limit("5.6.7.8")
    with pytest.raises(HTTPException):
        _check_login_rate_limit("5.6.7.8")   # blocked
    _check_login_rate_limit("9.9.9.9")       # other ip unaffected


def test_rate_limiter_expires_after_window(monkeypatch):
    import time
    frozen = [1000.0]
    monkeypatch.setattr(time, "time", lambda: frozen[0])
    for _ in range(10):
        _check_login_rate_limit("10.0.0.1")
    with pytest.raises(HTTPException):
        _check_login_rate_limit("10.0.0.1")
    # 61 seconds later the window has slid past the old attempts.
    frozen[0] += 61
    _check_login_rate_limit("10.0.0.1")      # no exception
