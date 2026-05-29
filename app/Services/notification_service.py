"""Service for handling email notifications and alerts."""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config.settings import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    SMTP_FROM,
    SMTP_ENABLED,
)

logger = logging.getLogger(__name__)


class NotificationService:
    """Handles sending email notifications."""

    @staticmethod
    def send_password_reset_email(to_email: str, reset_link: str) -> bool:
        """Send a password reset email to the user.

        If SMTP is not configured, this will gracefully fallback to logging
        the reset link in the console (useful for local development).

        Args:
            to_email: The recipient's email address.
            reset_link: The URL for resetting the password.

        Returns:
            True if the email was sent (or logged successfully), False on failure.
        """
        subject = "Réinitialisation de votre mot de passe - UDA Portal"
        
        # HTML Email Body
        html_content = f"""
        <html>
            <body style="font-family: 'Nunito', sans-serif; color: #333; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eef0f3; border-radius: 10px;">
                    <h2 style="color: #93DC5C; text-align: center;">UDA Portal</h2>
                    <p>Bonjour,</p>
                    <p>Vous avez demandé la réinitialisation de votre mot de passe. Veuillez cliquer sur le bouton ci-dessous pour créer un nouveau mot de passe :</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" style="background-color: #93DC5C; color: white; padding: 12px 24px; text-decoration: none; border-radius: 50px; font-weight: bold; display: inline-block;">Réinitialiser mon mot de passe</a>
                    </div>
                    <p>Si le bouton ne fonctionne pas, copiez-collez ce lien dans votre navigateur :</p>
                    <p style="word-break: break-all; color: #555;"><a href="{reset_link}">{reset_link}</a></p>
                    <p>Ce lien expirera dans 15 minutes.</p>
                    <p>Si vous n'avez pas demandé cette réinitialisation, veuillez ignorer cet e-mail.</p>
                    <hr style="border: none; border-top: 1px solid #eef0f3; margin-top: 30px;" />
                    <p style="font-size: 12px; text-align: center; color: #999;">Copyright &copy; 2026 UDA Portal</p>
                </div>
            </body>
        </html>
        """

        if not SMTP_ENABLED:
            logger.warning("SMTP non configuré. Lien de réinitialisation pour %s: %s", to_email, reset_link)
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = SMTP_FROM
            msg["To"] = to_email

            part = MIMEText(html_content, "html")
            msg.attach(part)

            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.ehlo()
            if SMTP_PORT == 587:
                server.starttls()
            
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)

            server.sendmail(SMTP_FROM, to_email, msg.as_string())
            server.quit()

            logger.info("E-mail de réinitialisation envoyé à %s", to_email)
            return True
        except Exception as e:
            logger.error("Échec de l'envoi de l'e-mail à %s: %s", to_email, e)
            # Fallback to logging so the user is not completely blocked
            logger.warning("Lien de réinitialisation (FALLBACK) pour %s: %s", to_email, reset_link)
            return False
