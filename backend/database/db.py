import os
import yaml
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import logging

from .models import Base
from .url import build_database_url

logger = logging.getLogger(__name__)


class DatabaseConfig:
    def __init__(self):
        self.config = self._load_config()
        self.database_url = build_database_url(
            os.environ,
            self.config.get("database", {}),
        )

    def _load_config(self):
        try:
            with open("config.yaml", "r", encoding="utf-8") as file:
                return yaml.safe_load(file) or {}
        except FileNotFoundError:
            logger.warning("config.yaml not found, using environment variables")
            return {}


class Database:
    def __init__(self):
        self.config = DatabaseConfig()
        self.engine = create_engine(
            self.config.database_url,
            pool_size=int(self.config.config.get("database", {}).get("pool_size", 10)),
            max_overflow=int(self.config.config.get("database", {}).get("max_overflow", 20)),
            echo=os.getenv("DEBUG", "false").lower() == "true",
            pool_pre_ping=True,
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )

    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")

    def drop_tables(self):
        Base.metadata.drop_all(bind=self.engine)
        logger.info("Database tables dropped")

    @contextmanager
    def get_session(self) -> Iterator[Session]:
        session = self.SessionLocal()
        try:
            yield session
        except Exception:
            session.rollback()
            logger.exception("Database session error")
            raise
        finally:
            session.close()


# Global database instance
db = Database()


def get_db() -> Iterator[Session]:
    """FastAPI dependency that always closes its session."""
    with db.get_session() as session:
        yield session


def init_database():
    """Initialize database with tables."""
    db.create_tables()
    logger.info("Database initialized successfully")
