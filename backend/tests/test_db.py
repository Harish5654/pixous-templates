"""Unit tests for backend/db.py — schema surface, session lifecycle, CRUD
round-trip on the isolated test database, and DATABASE_URL normalization."""
import importlib
import uuid

from db import (
    Base,
    ConfigRecord,
    TemplateRecord,
    UserRecord,
    VariableRecord,
    get_db,
    init_db,
)


def test_all_models_registered():
    tables = Base.metadata.tables
    for name in ("templates", "variables", "users", "config"):
        assert name in tables, f"missing table {name}"


def test_user_record_unique_email(make_user, db_session):
    user, _ = make_user(email="dup@pixoustech.com")
    dup = UserRecord(
        id=str(uuid.uuid4()), email=user.email, name="Other", role="Admin",
        hashed_password="x",
    )
    db_session.add(dup)
    import pytest
    with pytest.raises(Exception):  # IntegrityError on unique constraint
        db_session.commit()


def test_template_record_crud_roundtrip(db_session):
    tid = str(uuid.uuid4())
    payload = {"id": tid, "name": "CRUD Unit", "status": "Draft"}
    db_session.add(TemplateRecord(id=tid, payload=payload))
    db_session.commit()

    row = db_session.query(TemplateRecord).filter(TemplateRecord.id == tid).first()
    assert row.payload["name"] == "CRUD Unit"

    row.payload = {**row.payload, "status": "Published"}
    db_session.commit()
    assert db_session.query(TemplateRecord).filter(TemplateRecord.id == tid).first().payload["status"] == "Published"

    db_session.delete(row)
    db_session.commit()
    assert db_session.query(TemplateRecord).filter(TemplateRecord.id == tid).first() is None


def test_config_record_roundtrip(db_session):
    db_session.add(ConfigRecord(key="unit-key", payload={"n": 1}))
    db_session.commit()
    row = db_session.query(ConfigRecord).filter(ConfigRecord.key == "unit-key").first()
    assert row.payload == {"n": 1}
    db_session.delete(row)
    db_session.commit()


def test_get_db_yields_closed_session():
    gen = get_db()
    session = next(gen)
    assert session is not None
    gen.close()  # ensures finally branch (session.close) runs


def test_init_db_idempotent():
    # Calling init_db twice must not raise (CREATE TABLE IF NOT EXISTS path).
    init_db()
    init_db()


def test_postgres_scheme_normalized(monkeypatch):
    """postgres:// URLs (as injected by some hosts) must become postgresql://."""
    import db as db_module

    original_url = db_module.DATABASE_URL
    try:
        monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@host:5432/dbname")
        reloaded = importlib.reload(db_module)
        assert reloaded.DATABASE_URL == "postgresql://user:pass@host:5432/dbname"
        assert reloaded.engine.url.get_backend_name() == "postgresql"
    finally:
        monkeypatch.setenv("DATABASE_URL", original_url)
        importlib.reload(db_module)
        db_module.init_db()  # restore tables on the original engine
