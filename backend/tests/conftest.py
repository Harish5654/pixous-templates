"""Shared pytest fixtures for the backend unit-test suite.

Runs against an isolated temporary SQLite database — the real app.db and any
production data are never touched. Env vars are pinned *before* the app modules
(auth, db, seed, main) are imported so their module-level configuration points
at the test database with a known JWT secret.
"""
import os
import shutil
import tempfile
import uuid

import pytest

# --- Pinned before importing any app module ---
_TMPDIR = tempfile.mkdtemp(prefix="pixous-unit-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_TMPDIR, 'unit.db')}"
os.environ["JWT_SECRET"] = "unit-test-secret-not-for-production"
os.environ["ENVIRONMENT"] = "development"

from auth import hash_password  # noqa: E402
from db import SessionLocal, UserRecord, init_db  # noqa: E402

init_db()


@pytest.fixture(autouse=True, scope="session")
def _cleanup_tmpdir():
    yield
    shutil.rmtree(_TMPDIR, ignore_errors=True)


@pytest.fixture
def db_session():
    """Fresh DB session per test, rolled back after so tests stay isolated."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def make_user(db_session):
    """Factory that inserts a user and returns the UserRecord + plain password."""
    def _make(email=None, name="Test User", role="Employee", password="Password@123"):
        # Unique-by-default email keeps tests isolated against the shared file DB.
        if email is None:
            email = f"user-{uuid.uuid4().hex[:8]}@example.com"
        record = UserRecord(
            id=str(uuid.uuid4()),
            email=email,
            name=name,
            role=role,
            hashed_password=hash_password(password),
        )
        db_session.add(record)
        db_session.commit()
        return record, password
    return _make
