"""Audit repository for database operations on the audit_logs table."""

import logging
from typing import Optional

from database.connection import get_db
from app.Models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditRepository:
    """Repository handling all CRUD operations for AuditLog entities."""

    def log(
        self,
        user_id: Optional[int],
        action: str,
        entite: str,
        entite_id: Optional[int],
        statut: str,
        message: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """Create a new audit log entry.

        Args:
            user_id: The user's ID (None for system events).
            action: Description of the action performed.
            entite: Entity type affected.
            entite_id: ID of the affected entity.
            statut: Outcome ('succes' or 'erreur').
            message: Additional details or error message.
            ip_address: Client IP address.

        Returns:
            The created AuditLog object.
        """
        with get_db() as db:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                entite=entite,
                entite_id=entite_id,
                statut=statut,
                message=message,
                ip_address=ip_address,
            )
            db.add(audit_log)
            db.flush()
            db.expunge(audit_log)
            return audit_log

    def find_recent(self, limit: int = 100) -> list[AuditLog]:
        """Retrieve the most recent audit log entries.

        Args:
            limit: Maximum number of entries to return.

        Returns:
            A list of the most recent AuditLog objects.
        """
        with get_db() as db:
            logs = (
                db.query(AuditLog)
                .order_by(AuditLog.horodatage.desc())
                .limit(limit)
                .all()
            )
            for log_entry in logs:
                db.expunge(log_entry)
            return logs

    def find_by_user(self, user_id: int) -> list[AuditLog]:
        """Find all audit logs for a specific user.

        Args:
            user_id: The user's ID.

        Returns:
            A list of AuditLog objects for the user.
        """
        with get_db() as db:
            logs = (
                db.query(AuditLog)
                .filter(AuditLog.user_id == user_id)
                .order_by(AuditLog.horodatage.desc())
                .all()
            )
            for log_entry in logs:
                db.expunge(log_entry)
            return logs

    def find_errors(self, limit: int = 50) -> list[AuditLog]:
        """Find the most recent error audit log entries.

        Args:
            limit: Maximum number of entries to return.

        Returns:
            A list of AuditLog objects with statut='erreur'.
        """
        with get_db() as db:
            logs = (
                db.query(AuditLog)
                .filter(AuditLog.statut == "erreur")
                .order_by(AuditLog.horodatage.desc())
                .limit(limit)
                .all()
            )
            for log_entry in logs:
                db.expunge(log_entry)
            return logs
