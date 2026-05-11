"""Database initialization script.

Creates all tables and seeds a default admin user.
Run with: python database/init_db.py
"""

import sys
from pathlib import Path

# Add project root to sys.path for imports
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import bcrypt
from sqlalchemy import inspect

from config.settings import get_db_url
from config.logging_config import setup_logging
from database.base import Base
from database.connection import engine, SessionLocal

# Import all models so they register with Base.metadata
from models.user import User
from models.dataset import Dataset
from models.anomaly import Anomaly
from models.report import Report
from models.audit_log import AuditLog


def create_tables() -> None:
    """Create all tables defined in the ORM models."""
    print("[INFO] Création des tables dans la base de données...")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"[OK] Tables créées: {', '.join(tables)}")


def seed_admin_user() -> None:
    """Seed the database with a default admin user if one doesn't exist."""
    print("[INFO] Vérification de l'utilisateur admin par défaut...")

    session = SessionLocal()
    try:
        existing_admin = (
            session.query(User).filter_by(email="admin@uda.local").first()
        )

        if existing_admin:
            print("[INFO] L'utilisateur admin@uda.local existe déjà. Aucune action.")
            return

        # Hash the default password
        password_plain = "Admin1234!"
        password_hash = bcrypt.hashpw(
            password_plain.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        admin_user = User(
            nom="Administrateur",
            email="admin@uda.local",
            mot_de_passe=password_hash,
            role="admin",
            statut="actif",
            tentatives_echec=0,
        )

        session.add(admin_user)
        session.commit()
        print("[OK] Utilisateur admin créé:")
        print(f"     Email: admin@uda.local")
        print(f"     Mot de passe: Admin1234!")
        print(f"     Rôle: admin")
        print(f"     Statut: actif")
    except Exception as e:
        session.rollback()
        print(f"[ERREUR] Impossible de créer l'admin: {e}")
        raise
    finally:
        session.close()


def main() -> None:
    """Run database initialization."""
    print("=" * 60)
    print("  Universal Data Analyzer — Initialisation de la base")
    print("=" * 60)
    print()

    setup_logging()
    create_tables()
    print()
    seed_admin_user()

    print()
    print("=" * 60)
    print("  Initialisation terminée avec succès!")
    print("=" * 60)


if __name__ == "__main__":
    main()
