"""Admin API routes for system administration."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.Http.Middleware.dependencies import get_current_user, require_admin
from app.Http.Controllers.admin_controller import AdminController
from app.Http.Requests.user_schema import UserUpdateRequest

logger = logging.getLogger(__name__)
router = APIRouter()
_admin_ctrl = AdminController()


@router.get("/stats")
def get_system_stats(current_user: dict = Depends(require_admin)):
    """Get system-wide statistics (admin only).

    Returns:
        System statistics including user counts, data volume, etc.
    """
    stats = _admin_ctrl.get_statistiques_systeme()
    return stats


@router.get("/users")
def list_users(current_user: dict = Depends(require_admin)):
    """List all users in the system (admin only).

    Returns:
        A list of all users with their details.
    """
    users = _admin_ctrl.lister_utilisateurs()
    return {
        "users": [
            {
                "id": u.id,
                "nom": u.nom,
                "email": u.email,
                "role": u.role,
                "statut": u.statut,
                "cree_le": str(u.cree_le) if u.cree_le else None,
                "derniere_conn": str(u.derniere_conn) if u.derniere_conn else None,
            }
            for u in users
        ],
        "total": len(users),
    }


@router.post("/users")
def create_user(
    nom: str,
    email: str,
    password: str,
    role: str = "analyste",
    current_user: dict = Depends(require_admin),
):
    """Create a new user (admin only).

    Args:
        nom: User's full name.
        email: User's email.
        password: Plain-text password.
        role: User role (admin or analyste).

    Returns:
        The created user info.
    """
    try:
        user = _admin_ctrl.creer_utilisateur(nom, email, password, role)
        return {
            "id": user.id,
            "nom": user.nom,
            "email": user.email,
            "role": user.role,
            "message": f"Utilisateur '{email}' créé avec succès.",
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    request: UserUpdateRequest,
    current_user: dict = Depends(require_admin),
):
    """Update a user's profile (admin only).

    Args:
        user_id: The user's ID.
        request: Fields to update.

    Returns:
        The updated user info.
    """
    try:
        update_data = request.model_dump(exclude_unset=True)
        user = _admin_ctrl.modifier_utilisateur(user_id, **update_data)
        return {
            "id": user.id,
            "nom": user.nom,
            "email": user.email,
            "role": user.role,
            "statut": user.statut,
            "message": "Utilisateur mis à jour avec succès.",
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int, current_user: dict = Depends(require_admin)
):
    """Delete a user permanently (admin only).

    Args:
        user_id: The user's ID.
    """
    try:
        _admin_ctrl.supprimer_utilisateur(user_id)
        return {"message": f"Utilisateur ID={user_id} supprimé avec succès."}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.post("/users/{user_id}/reset-password")
def reset_password(
    user_id: int,
    new_password: str,
    current_user: dict = Depends(require_admin),
):
    """Reset a user's password (admin only).

    Args:
        user_id: The user's ID.
        new_password: The new plain-text password.
    """
    try:
        _admin_ctrl.reinitialiser_mdp(user_id, new_password)
        return {"message": f"Mot de passe réinitialisé pour user ID={user_id}."}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.get("/audit-logs")
def get_audit_logs(
    limit: int = 100,
    current_user: dict = Depends(require_admin),
):
    """Get recent audit logs (admin only).

    Args:
        limit: Maximum number of entries to return.

    Returns:
        A list of audit log entries.
    """
    logs = _admin_ctrl.get_audit_logs(limit=limit)
    return {
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "entite": log.entite,
                "statut": log.statut,
                "message": log.message,
                "horodatage": str(log.horodatage) if log.horodatage else None,
            }
            for log in logs
        ],
        "total": len(logs),
    }
