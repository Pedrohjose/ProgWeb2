"""Sessões da API de Pedro sobre os modelos SQLAlchemy da base de Carlos."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from banco import Base, SessionLocal as CarlosSessionLocal, engine as carlos_engine


if os.getenv("DATABASE_URL"):
    engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
else:
    engine = carlos_engine
    SessionLocal = CarlosSessionLocal


def get_db():
    with SessionLocal() as db:
        yield db
