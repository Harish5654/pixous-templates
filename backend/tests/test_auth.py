"""Unit tests for backend/auth.py — password hashing, JWT creation/validation,
and role-based access control. Pure unit tests: no HTTP server needed."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from jose import jwt

from auth import (
    JWT_ALGORITHM,
    JWT_EXPIRES_MINUTES,
    JWT_SECRET,
    create_access_token,
    get_current_user,
    hash_password,
    require_roles,
    verify_password,
)

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def test_password_hash_verify_roundtrip():
    hashed = hash_password("Secret@123")
    assert hashed != "Secret@123"                      # never stored in plaintext
    assert verify_password("Secret@123", hashed) is True


def test_password_hash_rejects_wrong_password():
    hashed = hash_password("Secret@123")
    assert verify_password("wrong-pass", hashed) is False


def test_password_hash_is_salted():
    assert hash_password("Secret@123") != hash_password("Secret@123")


# ---------------------------------------------------------------------------
# Token creation
# ---------------------------------------------------------------------------


def test_create_access_token_claims(make_user):
    user, _ = make_user(email="claims@pixoustech.com", role="Admin")
    token = create_access_token(user)
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    assert payload["sub"] == user.id
    assert payload["email"] == user.email
    assert payload["role"] == "Admin"


def test_create_access_token_expiry_is_24h(make_user):
    user, _ = make_user()
    payload = jwt.decode(create_access_token(user), JWT_SECRET, algorithms=[JWT_ALGORITHM])
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    expected = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRES_MINUTES)
    assert abs((exp - expected).total_seconds()) < 60


# ---------------------------------------------------------------------------
# get_current_user — every failure mode must raise 401
# ---------------------------------------------------------------------------


def test_get_current_user_missing_token(db_session):
    with pytest.raises(HTTPException) as e:
        get_current_user(token=None, db=db_session)
    assert e.value.status_code == 401


def test_get_current_user_garbage_token(db_session):
    with pytest.raises(HTTPException) as e:
        get_current_user(token="not.a.jwt", db=db_session)
    assert e.value.status_code == 401


def test_get_current_user_expired_token(db_session):
    expired = jwt.encode(
        {"sub": "x", "email": "a@b.c", "role": "Admin",
         "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
        JWT_SECRET, algorithm=JWT_ALGORITHM,
    )
    with pytest.raises(HTTPException) as e:
        get_current_user(token=expired, db=db_session)
    assert e.value.status_code == 401


def test_get_current_user_unknown_subject(db_session):
    token = jwt.encode(
        {"sub": "no-such-user", "email": "a@b.c", "role": "Admin",
         "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        JWT_SECRET, algorithm=JWT_ALGORITHM,
    )
    with pytest.raises(HTTPException) as e:
        get_current_user(token=token, db=db_session)
    assert e.value.status_code == 401


def test_get_current_user_alg_none_rejected(db_session):
    import base64
    import json
    import time

    def b64u(b):
        return base64.urlsafe_b64encode(b).rstrip(b"=")

    header = b64u(json.dumps({"alg": "none", "typ": "JWT"}).encode())
    payload = b64u(json.dumps({
        "sub": "x", "email": "a@b.c", "role": "Admin",
        "exp": int(time.time()) + 3600,
    }).encode())
    with pytest.raises(HTTPException) as e:
        get_current_user(token=f"{header.decode()}.{payload.decode()}.", db=db_session)
    assert e.value.status_code == 401


def test_get_current_user_valid_token(make_user, db_session):
    user, _ = make_user()
    token = create_access_token(user)
    result = get_current_user(token=token, db=db_session)
    assert result.id == user.id


# ---------------------------------------------------------------------------
# require_roles — RBAC gate
# ---------------------------------------------------------------------------


def test_require_roles_allows_matching_role():
    dep = require_roles("Admin")
    user = SimpleNamespace(role="Admin")
    assert dep(user=user) is user


def test_require_roles_rejects_other_role():
    dep = require_roles("Admin")
    with pytest.raises(HTTPException) as e:
        dep(user=SimpleNamespace(role="Editor"))
    assert e.value.status_code == 403


def test_require_roles_multiple_roles_any():
    dep = require_roles("Admin", "Editor")
    assert dep(user=SimpleNamespace(role="Editor")).role == "Editor"
    with pytest.raises(HTTPException):
        dep(user=SimpleNamespace(role="Employee"))
