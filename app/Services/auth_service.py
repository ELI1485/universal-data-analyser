"""Authentication service with JWT tokens and bcrypt password hashing.

Handles user login flow, password verification, token creation/validation,
and role-based access control.
"""

import logging
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from config.settings import (
    JWT_SECRET_KEY, 
    SESSION_TIMEOUT_MINUTES, 
    MAX_LOGIN_ATTEMPTS
)
from app.Repositories.user_repository import UserRepository
from app.Repositories.audit_repository import AuditRepository

logger = logging.getLogger(__name__)

_user_repo = UserRepository()
_audit_repo = AuditRepository()


def hash_password(plain: str) -> str:
    """Hash a plain-text password using bcrypt.

    Args:
        plain: The plain-text password to hash.

    Returns:
        The bcrypt-hashed password string.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a bcrypt hash.

    Args:
        plain: The plain-text password to check.
        hashed: The stored bcrypt hash.

    Returns:
        True if the password matches, False otherwise.
    """
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception as e:
        logger.error("Erreur lors de la vérification du mot de passe: %s", e)
        return False


def create_token(user_id: int, role: str) -> str:
    """Create a JWT token with user information and expiration.

    Args:
        user_id: The user's ID to encode in the token.
        role: The user's role to encode in the token.

    Returns:
        A signed JWT token string.
    """
    expiration = datetime.now(timezone.utc) + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": expiration,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
    return token


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token.

    Args:
        token: The JWT token string to verify.

    Returns:
        The decoded payload dictionary containing user_id and role.

    Raises:
        jwt.ExpiredSignatureError: If the token has expired.
        jwt.InvalidTokenError: If the token is invalid.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expiré")
        raise
    except jwt.InvalidTokenError as e:
        logger.warning("Token invalide: %s", e)
        raise


def generate_reset_token(email: str) -> str:
    """Generate a short-lived JWT token for password reset."""
    user = _user_repo.find_by_email(email)
    if not user:
        raise ValueError("Email inconnu.")
    
    expiration = datetime.now(timezone.utc) + timedelta(minutes=15)
    payload = {
        "email": email,
        "purpose": "password_reset",
        "exp": expiration,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")


def reset_password(token: str, new_password: str) -> bool:
    """Verify reset token and update password."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        if payload.get("purpose") != "password_reset":
            raise ValueError("Type de token invalide.")
        
        email = payload["email"]
        user = _user_repo.find_by_email(email)
        if not user:
            raise ValueError("Utilisateur introuvable.")
            
        password_hash = hash_password(new_password)
        _user_repo.update(user.id, mot_de_passe=password_hash)
        
        _audit_repo.log(
            user_id=user.id,
            action="password_reset",
            entite="user",
            entite_id=user.id,
            statut="succes",
            message="Mot de passe réinitialisé via lien",
            ip_address="127.0.0.1",
        )
        logger.info("Mot de passe réinitialisé pour %s", email)
        return True
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token de réinitialisation expiré")
        raise ValueError("Le lien de réinitialisation a expiré. Veuillez refaire une demande.")
    except jwt.InvalidTokenError:
        logger.warning("Token de réinitialisation invalide")
        raise ValueError("Le lien de réinitialisation est invalide ou corrompu.")


def get_current_user(token: str) -> dict:
    """Get the current user information from a valid token.

    Args:
        token: The JWT token string.

    Returns:
        A dict with 'user_id' and 'role' keys.

    Raises:
        jwt.ExpiredSignatureError: If the token has expired.
        jwt.InvalidTokenError: If the token is invalid.
    """
    payload = verify_token(token)
    return {"user_id": payload["user_id"], "role": payload["role"]}


def signup(nom: str, email: str, password: str, ip: str) -> dict:
    """Register a new user and return user information.

    Args:
        nom: The user's full name.
        email: The user's email address.
        password: The plain-text password.
        ip: The client's IP address for audit logging.

    Returns:
        A dict with the created user's information.

    Raises:
        ValueError: If the email is already in use or inputs are invalid.
    """
    # Check if email is already in use
    existing_user = _user_repo.find_by_email(email)
    if existing_user:
        logger.warning("Tentative d'inscription avec email existant: %s", email)
        _audit_repo.log(
            user_id=None,
            action="signup_echec",
            entite="user",
            entite_id=None,
            statut="erreur",
            message=f"Email déjà utilisé: {email}",
            ip_address=ip,
        )
        raise ValueError("Cet email est déjà utilisé.")

    # Hash the password
    password_hash = hash_password(password)

    # Create the user (default role: analyste)
    user = _user_repo.create(
        nom=nom,
        email=email,
        hashed_password=password_hash,
        role="analyste",
    )

    # Log successful signup
    _audit_repo.log(
        user_id=user.id,
        action="signup_succes",
        entite="user",
        entite_id=user.id,
        statut="succes",
        message=f"Nouvel utilisateur inscrit: {email}",
        ip_address=ip,
    )
    logger.info("Nouvel utilisateur inscrit: %s", email)

    return {
        "user_id": user.id,
        "nom": user.nom,
        "email": user.email,
        "role": user.role,
    }


def login(email: str, password: str, ip: str) -> str:
    """Authenticate a user and return a JWT token.

    Login flow:
    1. Find user by email
    2. Check statut != 'suspendu' or 'inactif'
    3. Check tentatives_echec < MAX_LOGIN_ATTEMPTS
    4. Verify password with bcrypt
    5. If wrong: increment_failed_attempts, log audit, raise
    6. If locked (>=5 fails): suspend account, raise
    7. If correct: reset_failed_attempts, update_last_login, log audit
    8. Return JWT token

    Args:
        email: The user's email address.
        password: The plain-text password.
        ip: The client's IP address for audit logging.

    Returns:
        A valid JWT token string.

    Raises:
        ValueError: If credentials are invalid or account is locked.
        PermissionError: If the account is suspended or inactive.
    """
    # Step 1: Find user by email
    user = _user_repo.find_by_email(email)
    if not user:
        logger.warning("Tentative de connexion avec email inconnu: %s", email)
        _audit_repo.log(
            user_id=None,
            action="login_echec",
            entite="user",
            entite_id=None,
            statut="erreur",
            message=f"Email inconnu: {email}",
            ip_address=ip,
        )
        raise ValueError("Email ou mot de passe incorrect.")

    # Step 2: Check account status
    if user.statut == "suspendu":
        logger.warning("Tentative de connexion sur compte suspendu: %s", email)
        _audit_repo.log(
            user_id=user.id,
            action="login_echec",
            entite="user",
            entite_id=user.id,
            statut="erreur",
            message="Compte suspendu",
            ip_address=ip,
        )
        raise PermissionError(
            "Votre compte est suspendu. Contactez un administrateur."
        )

    if user.statut == "inactif":
        logger.warning("Tentative de connexion sur compte inactif: %s", email)
        _audit_repo.log(
            user_id=user.id,
            action="login_echec",
            entite="user",
            entite_id=user.id,
            statut="erreur",
            message="Compte inactif",
            ip_address=ip,
        )
        raise PermissionError("Votre compte est inactif. Contactez un administrateur.")

    # Step 3: Check failed attempts
    if (user.tentatives_echec or 0) >= MAX_LOGIN_ATTEMPTS:
        # Step 6: Suspend account after too many failures
        _user_repo.update(user.id, statut="suspendu")
        _audit_repo.log(
            user_id=user.id,
            action="compte_suspendu",
            entite="user",
            entite_id=user.id,
            statut="erreur",
            message=f"Compte suspendu après {MAX_LOGIN_ATTEMPTS} tentatives échouées",
            ip_address=ip,
        )
        raise PermissionError(
            "Votre compte a été suspendu suite à trop de tentatives échouées. "
            "Contactez un administrateur."
        )

    # Step 4: Verify password
    if not verify_password(password, user.mot_de_passe):
        # Step 5: Increment failed attempts
        _user_repo.increment_failed_attempts(user.id)
        attempts = (user.tentatives_echec or 0) + 1
        _audit_repo.log(
            user_id=user.id,
            action="login_echec",
            entite="user",
            entite_id=user.id,
            statut="erreur",
            message=f"Mot de passe incorrect (tentative {attempts})",
            ip_address=ip,
        )
        logger.warning(
            "Mot de passe incorrect pour %s (tentative %d)", email, attempts
        )

        # Check if this attempt triggers suspension
        if attempts >= MAX_LOGIN_ATTEMPTS:
            _user_repo.update(user.id, statut="suspendu")
            _audit_repo.log(
                user_id=user.id,
                action="compte_suspendu",
                entite="user",
                entite_id=user.id,
                statut="erreur",
                message=f"Compte suspendu après {MAX_LOGIN_ATTEMPTS} tentatives",
                ip_address=ip,
            )
            raise PermissionError(
                "Votre compte a été suspendu suite à trop de tentatives échouées."
            )

        raise ValueError("Email ou mot de passe incorrect.")

    # Step 7: Success - reset attempts, update last login
    _user_repo.reset_failed_attempts(user.id)
    _user_repo.update_last_login(user.id)
    _audit_repo.log(
        user_id=user.id,
        action="login_succes",
        entite="user",
        entite_id=user.id,
        statut="succes",
        message="Connexion réussie",
        ip_address=ip,
    )
    logger.info("Connexion réussie pour %s", email)

    # Step 8: Return JWT token
    token = create_token(user.id, user.role)
    return token


def require_role(token: str, required_role: str) -> dict:
    """Verify that the token holder has the required role.

    Args:
        token: The JWT token string.
        required_role: The role that is required ('admin' or 'analyste').

    Returns:
        The user info dict if role matches.

    Raises:
        PermissionError: If the user's role doesn't match the required role.
        jwt.ExpiredSignatureError: If the token has expired.
        jwt.InvalidTokenError: If the token is invalid.
    """
    user_info = get_current_user(token)
    if user_info["role"] != required_role and user_info["role"] != "admin":
        raise PermissionError(
            f"Accès refusé. Rôle requis: {required_role}. "
            f"Votre rôle: {user_info['role']}."
        )
    return user_info
