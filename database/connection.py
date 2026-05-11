"""Database connection management using SQLAlchemy.

Creates the SQLAlchemy engine and session factory, and provides
a context manager for obtaining database sessions.
"""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config.settings import get_db_url

logger = logging.getLogger(__name__)

# Create the SQLAlchemy engine
try:
    engine = create_engine(
        get_db_url(),
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False,
    )
    logger.info("Moteur de base de données créé avec succès.")
except Exception as e:
    logger.error("Erreur lors de la création du moteur de base de données: %s", e)
    raise

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Provide a transactional database session as a context manager.

    Yields:
        A SQLAlchemy Session instance.

    Example:
        with get_db() as db:
            user = db.query(User).filter_by(email=email).first()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error("Erreur de session DB — rollback effectué: %s", e)
        raise
    finally:
        session.close()
