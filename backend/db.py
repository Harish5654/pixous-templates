import os

from sqlalchemy import create_engine, Column, String, Integer, JSON
from sqlalchemy.orm import declarative_base, sessionmaker

# Render (and most Postgres hosts) inject DATABASE_URL automatically once a
# database is linked to the service. Falls back to a local SQLite file when
# unset, so local dev needs no extra setup.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./app.db")

# Some hosts hand out URLs starting with "postgres://", which SQLAlchemy 1.4+
# no longer accepts — it requires the "postgresql://" scheme.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# check_same_thread is a SQLite-only connect arg; Postgres rejects it.
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class TemplateRecord(Base):
    __tablename__ = "templates"
    id = Column(String, primary_key=True)
    payload = Column(JSON, nullable=False)


class VariableRecord(Base):
    __tablename__ = "variables"
    id = Column(String, primary_key=True)
    payload = Column(JSON, nullable=False)


class UserRecord(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)


class ConfigRecord(Base):
    """Generic key -> JSON document store. Each independent config domain
    (master data, and future ones like branding or AI settings) gets its own
    key/row rather than being merged into one shared blob."""
    __tablename__ = "config"
    key = Column(String, primary_key=True)
    payload = Column(JSON, nullable=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
