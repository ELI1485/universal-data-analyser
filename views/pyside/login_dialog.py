"""PySide6 login dialog for user authentication."""

import sys
from pathlib import Path

_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from controllers.auth_controller import AuthController


class LoginDialog(QDialog):
    """Login dialog for PySide6 desktop application.

    Emits login_success signal with token and role on successful authentication.
    """

    login_success = Signal(dict)

    def __init__(self, parent=None) -> None:
        """Initialize the login dialog.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self._auth_ctrl = AuthController()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the dialog UI components."""
        self.setWindowTitle("Universal Data Analyzer — Connexion")
        self.setFixedSize(400, 300)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(40, 30, 40, 30)

        # Title
        title_label = QLabel("📊 Universal Data Analyzer")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        subtitle_label = QLabel("Connexion")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        # Email field
        email_label = QLabel("Email:")
        layout.addWidget(email_label)
        self._email_input = QLineEdit()
        self._email_input.setPlaceholderText("admin@uda.local")
        layout.addWidget(self._email_input)

        # Password field
        password_label = QLabel("Mot de passe:")
        layout.addWidget(password_label)
        self._password_input = QLineEdit()
        self._password_input.setPlaceholderText("Entrez votre mot de passe")
        self._password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_input.returnPressed.connect(self._on_login_clicked)
        layout.addWidget(self._password_input)

        # Error label
        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: red;")
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.setWordWrap(True)
        layout.addWidget(self._error_label)

        # Login button
        self._login_btn = QPushButton("Se connecter")
        self._login_btn.setStyleSheet(
            "QPushButton { background-color: #1a237e; color: white; "
            "padding: 8px; border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background-color: #283593; }"
        )
        self._login_btn.clicked.connect(self._on_login_clicked)
        layout.addWidget(self._login_btn)

        layout.addStretch()

    def _on_login_clicked(self) -> None:
        """Handle login button click."""
        email = self._email_input.text().strip()
        password = self._password_input.text()

        if not email or not password:
            self._error_label.setText("Veuillez remplir tous les champs.")
            return

        self._error_label.setText("")
        self._login_btn.setEnabled(False)
        self._login_btn.setText("Connexion en cours...")

        try:
            result = self._auth_ctrl.login(email, password, ip="127.0.0.1")
            self.login_success.emit(result)
            self.accept()

        except ValueError as e:
            self._error_label.setText(str(e))
        except PermissionError as e:
            self._error_label.setText(str(e))
        except Exception as e:
            self._error_label.setText(f"Erreur: {str(e)}")
        finally:
            self._login_btn.setEnabled(True)
            self._login_btn.setText("Se connecter")
