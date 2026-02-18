import os
import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging
from .models import Base

logger = logging.getLogger(__name__)

class DatabaseConfig:
    def __init__(self):
        self.config = self._load_config()
        self.database_url = self._build_database_url()
        
    def _load_config(self):
        try:
            with open('config.yaml', 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.warning("config.yaml not found, using environment variables")
            return {}
    
    def _build_database_url(self):
        # Use environment variables if available, otherwise use config.yaml
        db_config = self.config.get('database', {})
        
        host = os.getenv('DB_HOST', db_config.get('host', 'localhost'))
        port = os.getenv('DB_PORT', db_config.get('port', 5432))
        name = os.getenv('DB_NAME', db_config.get('name', 'sovereign_ai_arsenal'))
        user = os.getenv('DB_USER', db_config.get('user', 'postgres'))
        password = os.getenv('DB_PASSWORD', db_config.get('password', 'password'))
        
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"

class Database:
    def __init__(self):
        self.config = DatabaseConfig()
        self.engine = create_engine(
            self.config.database_url,
            pool_size=self.config.config.get('database', {}).get('pool_size', 10),
            max_overflow=self.config.config.get('database', {}).get('max_overflow', 20),
            echo=os.getenv('DEBUG', 'false').lower() == 'true'
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")
    
    def drop_tables(self):
        Base.metadata.drop_all(bind=self.engine)
        logger.info("Database tables dropped")
    
    def get_session(self) -> Generator[Session, None, None]:
        db = self.SessionLocal()
        try:
            yield db
        except Exception as e:
            logger.error(f"Database session error: {e}")
            db.rollback()
            raise
        finally:
            db.close()

# Global database instance
db = Database()

def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session"""
    return db.get_db()

def init_database():
    """Initialize database with tables"""
    try:
        db.create_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise