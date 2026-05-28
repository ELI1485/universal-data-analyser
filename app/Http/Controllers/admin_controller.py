"""Admin controller for system administration operations."""

import logging
from typing import Optional

from app.Models.user import User
from app.Models.audit_log import AuditLog
from app.Repositories.user_repository import UserRepository
from app.Repositories.dataset_repository import DatasetRepository
from app.Repositories.report_repository import ReportRepository
from app.Repositories.anomaly_repository import AnomalyRepository
from app.Repositories.audit_repository import AuditRepository
from app.Services.auth_service import hash_password
from app.Services.audit_service import log_action

logger = logging.getLogger(__name__)

_user_repo = UserRepository()
_dataset_repo = DatasetRepository()
_report_repo = ReportRepository()
_anomaly_repo = AnomalyRepository()
_audit_repo = AuditRepository()


class AdminController:
    """Controller for administrative operations (admin role only)."""

    def get_statistiques_systeme(self) -> dict:
        """Get system-wide statistics for the admin dashboard.

        Returns:
            A dict with total_users, active_users, total_analyses,
            total_reports, total_data_mo, anomalies_30j, llm_calls_month.
        """
        users = _user_repo.find_all()
        datasets = _dataset_repo.find_all()
        reports = _report_repo.find_all()
        anomalies_30j = _anomaly_repo.count_recent(days=30)

        active_users = sum(1 for u in users if u.statut == "actif")
        total_data_mo = sum(d.taille_mo for d in datasets if d.taille_mo)
        total_analyses = sum(1 for d in datasets if d.statut == "traite")

        stats = {
            "total_users": len(users),
            "active_users": active_users,
            "total_analyses": total_analyses,
            "total_datasets": len(datasets),
            "total_reports": len(reports),
            "total_data_mo": round(total_data_mo, 2),
            "anomalies_30j": anomalies_30j,
            "llm_calls_month": 0,  # Would need a counter in production
        }

        logger.info("Statistiques système récupérées")
        return stats

    def lister_utilisateurs(self) -> list[User]:
        """List all users in the system.

        Returns:
            A list of all User objects.
        """
        users = _user_repo.find_all()
        logger.info("Liste utilisateurs: %d résultats", len(users))
        return users

    def creer_utilisateur(
        self, nom: str, email: str, password: str, role: str
    ) -> User:
        """Create a new user account.

        Args:
            nom: The user's full name.
            email: The user's email address.
            password: The plain-text password (will be hashed).
            role: The user's role ('admin' or 'analyste').

        Returns:
            The newly created User object.

        Raises:
            ValueError: If the email already exists or role is invalid.
        """
        if role not in ("admin", "analyste"):
            raise ValueError(f"Rôle invalide: '{role}'. Utilisez 'admin' ou 'analyste'.")

        existing = _user_repo.find_by_email(email)
        if existing:
            raise ValueError(f"Un utilisateur avec l'email '{email}' existe déjà.")

        hashed = hash_password(password)
        user = _user_repo.create(nom, email, hashed, role)

        log_action(
            user_id=None,
            action="creer_utilisateur",
            entite="user",
            entite_id=user.id,
            statut="succes",
            message=f"Utilisateur '{email}' créé avec rôle '{role}'",
            ip=None,
        )

        logger.info("Utilisateur créé: %s (%s)", email, role)
        return user

    def modifier_utilisateur(self, user_id: int, **kwargs) -> User:
        """Update user fields.

        Args:
            user_id: The user's ID.
            **kwargs: Fields to update (nom, email, role, statut).

        Returns:
            The updated User object.

        Raises:
            ValueError: If user not found.
        """
        user = _user_repo.update(user_id, **kwargs)
        if not user:
            raise ValueError(f"Utilisateur avec ID={user_id} introuvable.")

        log_action(
            user_id=None,
            action="modifier_utilisateur",
            entite="user",
            entite_id=user_id,
            statut="succes",
            message=f"Utilisateur ID={user_id} modifié: {list(kwargs.keys())}",
            ip=None,
        )

        logger.info("Utilisateur ID=%d modifié", user_id)
        return user

    def desactiver_utilisateur(self, user_id: int) -> bool:
        """Deactivate a user account.

        Args:
            user_id: The user's ID.

        Returns:
            True if deactivated successfully.

        Raises:
            ValueError: If user not found.
        """
        user = _user_repo.update(user_id, statut="inactif")
        if not user:
            raise ValueError(f"Utilisateur avec ID={user_id} introuvable.")

        log_action(
            user_id=None,
            action="desactiver_utilisateur",
            entite="user",
            entite_id=user_id,
            statut="succes",
            message=f"Utilisateur ID={user_id} désactivé",
            ip=None,
        )

        logger.info("Utilisateur ID=%d désactivé", user_id)
        return True

    def supprimer_utilisateur(self, user_id: int) -> bool:
        """Delete a user account permanently.

        Args:
            user_id: The user's ID.

        Returns:
            True if deleted.

        Raises:
            ValueError: If user not found.
        """
        result = _user_repo.delete(user_id)
        if not result:
            raise ValueError(f"Utilisateur avec ID={user_id} introuvable.")

        log_action(
            user_id=None,
            action="supprimer_utilisateur",
            entite="user",
            entite_id=user_id,
            statut="succes",
            message=f"Utilisateur ID={user_id} supprimé",
            ip=None,
        )

        logger.info("Utilisateur ID=%d supprimé", user_id)
        return True

    def reinitialiser_mdp(self, user_id: int, new_password: str) -> bool:
        """Reset a user's password.

        Args:
            user_id: The user's ID.
            new_password: The new plain-text password (will be hashed).

        Returns:
            True if password was reset.

        Raises:
            ValueError: If user not found.
        """
        hashed = hash_password(new_password)
        user = _user_repo.update(user_id, mot_de_passe=hashed, tentatives_echec=0)
        if not user:
            raise ValueError(f"Utilisateur avec ID={user_id} introuvable.")

        # Also reactivate if suspended
        if user.statut == "suspendu":
            _user_repo.update(user_id, statut="actif")

        log_action(
            user_id=None,
            action="reinitialiser_mdp",
            entite="user",
            entite_id=user_id,
            statut="succes",
            message=f"Mot de passe réinitialisé pour user ID={user_id}",
            ip=None,
        )

        logger.info("Mot de passe réinitialisé pour user ID=%d", user_id)
        return True

    def get_audit_logs(self, limit: int = 100) -> list[AuditLog]:
        """Get recent audit logs.

        Args:
            limit: Maximum number of log entries to return.

        Returns:
            A list of AuditLog objects.
        """
        logs = _audit_repo.find_recent(limit=limit)
        return logs

    def get_error_logs(self, limit: int = 50) -> list[AuditLog]:
        """Get recent error audit logs.

        Args:
            limit: Maximum number of error entries to return.

        Returns:
            A list of AuditLog objects with statut='erreur'.
        """
        logs = _audit_repo.find_errors(limit=limit)
        return logs
