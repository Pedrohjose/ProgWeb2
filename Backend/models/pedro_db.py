"""Sessões da API de Pedro sobre os modelos SQLAlchemy da base de Carlos."""

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from banco import Base, SessionLocal as CarlosSessionLocal, engine as carlos_engine


if os.getenv("MYSQL_PASSWORD"):
    url = URL.create(
        "mysql+mysqlconnector",
        username=os.getenv("MYSQL_USER", "root"),
        password=os.environ["MYSQL_PASSWORD"],
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        database=os.getenv("MYSQL_DATABASE", "estok"),
    )
    engine = create_engine(url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
elif os.getenv("DATABASE_URL"):
    engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
else:
    engine = carlos_engine
    SessionLocal = CarlosSessionLocal


def get_db():
    with SessionLocal() as db:
        yield db
