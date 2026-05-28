"""Email notification service for alerts and reports.

Sends email notifications via SMTP when anomalies are detected,
reports are generated, or new users sign up. Gracefully degrades
if SMTP is not configured.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

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
    """Service for sending email notifications.

    Gracefully handles missing SMTP configuration by logging
    warnings instead of raising errors.
    """

    def __init__(self) -> None:
        """Initialize the notification service."""
        self._enabled = SMTP_ENABLED
        if not self._enabled:
            logger.info(
                "Service de notification désactivé (SMTP non configuré)."
            )

    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
    ) -> bool:
        """Send an email via SMTP.

        Args:
            to_email: Recipient email address.
            subject: Email subject line.
            html_body: HTML content of the email.

        Returns:
            True if sent successfully, False otherwise.
        """
        if not self._enabled:
            logger.debug(
                "Email non envoyé (SMTP désactivé): to=%s, subject=%s",
                to_email, subject,
            )
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = SMTP_FROM
            msg["To"] = to_email
            msg["Subject"] = subject

            html_part = MIMEText(html_body, "html", "utf-8")
            msg.attach(html_part)

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.ehlo()
                if SMTP_PORT != 25:
                    server.starttls()
                    server.ehlo()
                if SMTP_USER and SMTP_PASSWORD:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM, to_email, msg.as_string())

            logger.info("Email envoyé à %s: %s", to_email, subject)
            return True

        except Exception as e:
            logger.error("Erreur envoi email à %s: %s", to_email, e)
            return False

    def envoyer_alerte_anomalies(
        self,
        user_email: str,
        dataset_name: str,
        anomaly_count: int,
        top_anomalies: list[dict],
    ) -> bool:
        """Send an anomaly alert email.

        Args:
            user_email: Recipient email.
            dataset_name: Name of the analyzed dataset.
            anomaly_count: Total number of anomalies detected.
            top_anomalies: Top 5 anomalies for the email body.

        Returns:
            True if sent successfully.
        """
        subject = f"UDA — {anomaly_count} anomalies detectees dans '{dataset_name}'"

        anomalies_html = ""
        for a in top_anomalies[:5]:
            anomalies_html += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{a.get('colonne', 'N/A')}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">Ligne {a.get('ligne', 'N/A')}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{a.get('score', 0):.2f}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{a.get('type', 'N/A')}</td>
            </tr>
            """

        html_body = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #93DC5C, #6db33f); padding: 30px; border-radius: 12px 12px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 24px;">Alerte Anomalies</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0;">Universal Data Analyzer</p>
            </div>
            <div style="background: white; padding: 30px; border: 1px solid #eee; border-radius: 0 0 12px 12px;">
                <p style="color: #333;">Bonjour,</p>
                <p style="color: #333;">
                    La détection d'anomalies sur le dataset <strong>"{dataset_name}"</strong> a identifié
                    <strong style="color: #e74c3c;">{anomaly_count} anomalies</strong>.
                </p>

                <h3 style="color: #333; border-bottom: 2px solid #93DC5C; padding-bottom: 8px;">
                    Top anomalies détectées
                </h3>
                <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                    <thead>
                        <tr style="background: #f8f9fa;">
                            <th style="padding: 10px; text-align: left;">Colonne</th>
                            <th style="padding: 10px; text-align: left;">Ligne</th>
                            <th style="padding: 10px; text-align: left;">Score</th>
                            <th style="padding: 10px; text-align: left;">Algorithme</th>
                        </tr>
                    </thead>
                    <tbody>
                        {anomalies_html}
                    </tbody>
                </table>

                <p style="color: #666; margin-top: 20px; font-size: 13px;">
                    Connectez-vous à UDA pour voir l'analyse complète et générer un rapport.
                </p>
            </div>
        </div>
        """
        return self._send_email(user_email, subject, html_body)

    def envoyer_rapport_pret(
        self,
        user_email: str,
        report_format: str,
        dataset_name: str,
    ) -> bool:
        """Send a notification that a report is ready.

        Args:
            user_email: Recipient email.
            report_format: Report format (pdf or excel).
            dataset_name: Name of the dataset.

        Returns:
            True if sent successfully.
        """
        subject = f"UDA — Rapport {report_format.upper()} pret pour '{dataset_name}'"

        html_body = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #93DC5C, #6db33f); padding: 30px; border-radius: 12px 12px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 24px;">Rapport pret</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0;">Universal Data Analyzer</p>
            </div>
            <div style="background: white; padding: 30px; border: 1px solid #eee; border-radius: 0 0 12px 12px;">
                <p style="color: #333;">Bonjour,</p>
                <p style="color: #333;">
                    Votre rapport <strong>{report_format.upper()}</strong> pour le dataset
                    <strong>"{dataset_name}"</strong> a ete genere avec succes.
                </p>
                <div style="background: #f0fdf4; border-left: 4px solid #93DC5C; padding: 15px; margin: 20px 0; border-radius: 4px;">
                    <p style="color: #333; margin: 0;">
                        Le rapport est pret a etre telecharge depuis votre espace UDA.
                    </p>
                </div>
                <p style="color: #666; font-size: 13px;">
                    Connectez-vous a UDA pour telecharger votre rapport.
                </p>
            </div>
        </div>
        """
        return self._send_email(user_email, subject, html_body)

    def envoyer_bienvenue(self, user_email: str, nom: str) -> bool:
        """Send a welcome email to a new user.

        Args:
            user_email: New user's email.
            nom: New user's name.

        Returns:
            True if sent successfully.
        """
        subject = "Bienvenue sur Universal Data Analyzer"

        html_body = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #93DC5C, #6db33f); padding: 30px; border-radius: 12px 12px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 24px;">Bienvenue</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0;">Universal Data Analyzer</p>
            </div>
            <div style="background: white; padding: 30px; border: 1px solid #eee; border-radius: 0 0 12px 12px;">
                <p style="color: #333;">Bonjour <strong>{nom}</strong>,</p>
                <p style="color: #333;">
                    Votre compte a ete cree avec succes sur Universal Data Analyzer.
                </p>
                <h3 style="color: #333; border-bottom: 2px solid #93DC5C; padding-bottom: 8px;">
                    Ce que vous pouvez faire
                </h3>
                <ul style="color: #333; line-height: 2;">
                    <li>Importer des fichiers CSV/Excel</li>
                    <li>Lancer des analyses statistiques et detection d'anomalies</li>
                    <li>Obtenir des insights IA via Gemini</li>
                    <li>Generer des rapports PDF/Excel professionnels</li>
                    <li>Comparer des versions de datasets</li>
                </ul>
                <p style="color: #666; font-size: 13px; margin-top: 20px;">
                    Connectez-vous des maintenant pour commencer.
                </p>
            </div>
        </div>
        """
        return self._send_email(user_email, subject, html_body)
