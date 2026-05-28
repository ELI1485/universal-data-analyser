"""Audit service wrapping AuditRepository with file logging.

Provides methods to log audit events both to the database and the
dedicated audit log file.
"""

import logging
import traceback
from typing import Optional

from config.logging_config import get_audit_logger
from app.Repositories.audit_repository import AuditRepository
from app.Models.audit_log import AuditLog

logger = logging.getLogger(__name__)

_audit_repo = AuditRepository()


def log_action(
    user_id: Optional[int],
    action: str,
    entite: str,
    entite_id: Optional[int],
    statut: str,
    message: Optional[str] = None,
    ip: Optional[str] = None,
) -> AuditLog:
    """Log an audit event to both the database and audit log file.

    Args:
        user_id: The acting user's ID (None for system events).
        action: Description of the action performed.
        entite: Entity type affected (e.g., 'dataset', 'user').
        entite_id: ID of the affected entity.
        statut: Outcome ('succes' or 'erreur').
        message: Additional message or details.
        ip: Client IP address.

    Returns:
        The created AuditLog database record.
    """
    # Write to audit log file
    audit_logger = get_audit_logger()
    log_message = (
        f"[AUDIT] user_id={user_id} | action={action} | "
        f"entite={entite} | entite_id={entite_id} | "
        f"statut={statut} | message={message} | ip={ip}"
    )

    if statut == "succes":
        audit_logger.info(log_message)
    else:
        audit_logger.warning(log_message)

    # Write to database
    try:
        audit_log = _audit_repo.log(
            user_id=user_id,
            action=action,
            entite=entite,
            entite_id=entite_id,
            statut=statut,
            message=message,
            ip_address=ip,
        )
        return audit_log
    except Exception as e:
        logger.error("Erreur lors de l'enregistrement de l'audit en DB: %s", e)
        # Return a non-persisted object to avoid breaking the caller
        return AuditLog(
            user_id=user_id,
            action=action,
            entite=entite,
            entite_id=entite_id,
            statut=statut,
            message=message,
            ip_address=ip,
        )


def log_error(
    user_id: Optional[int],
    action: str,
    error: Exception,
    ip: Optional[str] = None,
) -> AuditLog:
    """Log an error event to both the database and audit log file.

    Args:
        user_id: The acting user's ID (None for system events).
        action: Description of the action that caused the error.
        error: The exception that occurred.
        ip: Client IP address.

    Returns:
        The created AuditLog database record.
    """
    error_message = f"{type(error).__name__}: {str(error)}"
    tb = traceback.format_exc()

    # Write detailed error to audit log file
    audit_logger = get_audit_logger()
    audit_logger.error(
        "[AUDIT-ERROR] user_id=%s | action=%s | error=%s | ip=%s\n%s",
        user_id,
        action,
        error_message,
        ip,
        tb,
    )

    # Write to database (truncate message if too long)
    db_message = error_message[:500] if len(error_message) > 500 else error_message

    try:
        audit_log = _audit_repo.log(
            user_id=user_id,
            action=action,
            entite="system",
            entite_id=None,
            statut="erreur",
            message=db_message,
            ip_address=ip,
        )
        return audit_log
    except Exception as db_error:
        logger.error(
            "Erreur lors de l'enregistrement de l'erreur d'audit en DB: %s", db_error
        )
        return AuditLog(
            user_id=user_id,
            action=action,
            entite="system",
            entite_id=None,
            statut="erreur",
            message=db_message,
            ip_address=ip,
        )
