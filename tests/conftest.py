"""Pytest fixtures for Universal Data Analyzer tests."""

import os
import sys
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Set minimal env vars before importing project modules
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "3306")
os.environ.setdefault("DB_NAME", "test_db")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key_for_testing_only_32chars")
os.environ.setdefault("GEMINI_API_KEY", "test_key")
os.environ.setdefault("LLM_PROVIDER", "gemini")
os.environ.setdefault("LOG_DIR", "./test_logs")
os.environ.setdefault("EXPORT_DIR", "./test_exports")

from database.base import Base
from models.user import User
from models.dataset import Dataset
from models.anomaly import Anomaly
from models.report import Report
from models.audit_log import AuditLog
from services.auth_service import hash_password, create_token


@pytest.fixture
def db_session():
    """Provide an in-memory SQLite session for tests.

    Creates all tables, yields the session, then tears down.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_dataframe():
    """Create a 100-row DataFrame with mixed columns for testing.

    Includes:
    - Numeric columns (with some NaN and outliers)
    - Categorical columns (with some NaN)
    - A date column
    - Duplicate rows
    """
    np.random.seed(42)
    n = 100

    df = pd.DataFrame(
        {
            "age": np.random.randint(18, 80, n).astype(float),
            "salaire": np.random.normal(50000, 15000, n),
            "score": np.random.uniform(0, 100, n),
            "departement": np.random.choice(
                ["RH", "IT", "Finance", "Marketing", "Ventes"], n
            ),
            "ville": np.random.choice(
                ["Paris", "Lyon", "Marseille", "Toulouse", "Nantes"], n
            ),
            "date_embauche": pd.date_range("2020-01-01", periods=n, freq="W"),
        }
    )

    # Add some NaN values
    df.loc[5, "age"] = np.nan
    df.loc[10, "salaire"] = np.nan
    df.loc[15, "departement"] = np.nan
    df.loc[20, "ville"] = np.nan

    # Add outliers
    df.loc[0, "salaire"] = 500000  # Very high salary
    df.loc[1, "salaire"] = -10000  # Negative salary
    df.loc[2, "age"] = 150  # Impossible age

    # Add duplicate rows
    df = pd.concat([df, df.iloc[[3, 4, 5]]], ignore_index=True)

    return df


@pytest.fixture
def test_user_admin(db_session):
    """Create a test admin user.

    Returns:
        A User object with role='admin' persisted in the test DB.
    """
    hashed = hash_password("AdminTest123!")
    user = User(
        nom="Admin Test",
        email="admin@test.local",
        mot_de_passe=hashed,
        role="admin",
        statut="actif",
        tentatives_echec=0,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_analyste(db_session):
    """Create a test analyste user.

    Returns:
        A User object with role='analyste' persisted in the test DB.
    """
    hashed = hash_password("AnalysteTest123!")
    user = User(
        nom="Analyste Test",
        email="analyste@test.local",
        mot_de_passe=hashed,
        role="analyste",
        statut="actif",
        tentatives_echec=0,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_token_admin(test_user_admin):
    """Create a JWT token for the admin test user.

    Returns:
        A valid JWT token string.
    """
    return create_token(test_user_admin.id, test_user_admin.role)


@pytest.fixture
def auth_token_analyste(test_user_analyste):
    """Create a JWT token for the analyste test user.

    Returns:
        A valid JWT token string.
    """
    return create_token(test_user_analyste.id, test_user_analyste.role)
