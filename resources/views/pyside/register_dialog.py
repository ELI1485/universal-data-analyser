"""PySide6 registration dialog for new user signup.

Mirrors the Streamlit signup page (nom, email, mot de passe, confirmation)
and the visual design of :class:`LoginDialog` so the desktop and web
front-ends stay in sync.
"""

import sys
import urllib.request
from pathlib import Path

_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
    QFrame,
)
from PySide6.QtCore import Signal, Qt

from app.Http.Controllers.auth_controller import AuthController


class RegisterDialog(QDialog):
    """Registration dialog for the PySide6 desktop application.

    Emits ``register_success`` with the created user's info dict on a
    successful signup, and ``login_requested`` when the user chooses to go
    back to the login screen.
    """

    register_success = Signal(dict)
    login_requested = Signal()

    def __init__(self, parent=None) -> None:
        """Initialize the registration dialog.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self._auth_ctrl = AuthController()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the dialog UI components."""
        self.setWindowTitle("Universal Data Analyzer — Inscription")
        self.setFixedSize(960, 560)
        self.setWindowFlags(Qt.WindowType.Dialog)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        container = QFrame(self)
        container.setObjectName("MainContainer")
        container.setStyleSheet(
            "#MainContainer {"
            "  background-color: white;"
            "  border-radius: 20px;"
            "}"
        )
        main_layout.addWidget(container)

        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)

        # --- LEFT PANEL (decorative, same look as login) ---
        left_panel = QWidget()
        left_panel.setFixedWidth(480)
        left_layout = QGridLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        bg_label = QLabel()
        bg_label.setScaledContents(True)
        try:
            url = "https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=600&auto=format&fit=crop"
            data = urllib.request.urlopen(url, timeout=3).read()
            from PySide6.QtGui import QPixmap

            pixmap = QPixmap()
            pixmap.loadFromData(data)
            bg_label.setPixmap(pixmap)
        except Exception:
            bg_label.setStyleSheet(
                "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #93DC5C, stop:1 #4e732d);"
                " border-top-left-radius: 20px; border-bottom-left-radius: 20px;"
            )
        left_layout.addWidget(bg_label, 0, 0)

        overlay = QFrame()
        overlay.setStyleSheet(
            "background-color: rgba(0, 0, 0, 0.3);"
            " border-top-left-radius: 20px; border-bottom-left-radius: 20px;"
        )
        left_layout.addWidget(overlay, 0, 0)

        logo_box = QFrame()
        logo_box.setFixedSize(200, 180)
        logo_box.setStyleSheet(
            "QFrame {"
            "  background-color: rgba(147, 220, 92, 0.95);"
            "  border-radius: 25px;"
            "}"
        )
        logo_layout = QVBoxLayout(logo_box)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel("📊")
        icon_label.setStyleSheet("font-size: 60px; background: transparent;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(icon_label)

        brand_label = QLabel("Bienvenue")
        brand_label.setStyleSheet(
            "color: white; font-weight: bold; font-size: 20px; background: transparent;"
        )
        brand_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(brand_label)

        left_layout.addWidget(logo_box, 0, 0, Qt.AlignmentFlag.AlignCenter)
        h_layout.addWidget(left_panel)

        # --- RIGHT PANEL (form) ---
        right_panel = QFrame()
        right_panel.setObjectName("RightPanel")
        right_panel.setStyleSheet(
            "#RightPanel { background-color: white;"
            " border-top-right-radius: 20px; border-bottom-right-radius: 20px; }"
        )
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(50, 20, 50, 30)

        right_layout.addStretch()

        title_label = QLabel("Inscription")
        title_label.setStyleSheet(
            "font-size: 24px; color: #2c3e50; font-weight: 300; margin-bottom: 15px;"
        )
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(title_label)

        self._nom_input = QLineEdit()
        self._nom_input.setPlaceholderText("Nom complet")
        self._nom_input.setFixedHeight(48)
        right_layout.addWidget(self._nom_input)

        right_layout.addSpacing(8)

        self._email_input = QLineEdit()
        self._email_input.setPlaceholderText("Email")
        self._email_input.setFixedHeight(48)
        right_layout.addWidget(self._email_input)

        right_layout.addSpacing(8)

        self._password_input = QLineEdit()
        self._password_input.setPlaceholderText("Mot de passe")
        self._password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_input.setFixedHeight(48)
        right_layout.addWidget(self._password_input)

        right_layout.addSpacing(8)

        self._confirm_input = QLineEdit()
        self._confirm_input.setPlaceholderText("Confirmer le mot de passe")
        self._confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._confirm_input.setFixedHeight(48)
        self._confirm_input.returnPressed.connect(self._on_register_clicked)
        right_layout.addWidget(self._confirm_input)

        right_layout.addSpacing(12)

        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: #e74c3c; font-weight: bold; background: transparent;")
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.setWordWrap(True)
        right_layout.addWidget(self._error_label)

        self._register_btn = QPushButton("S'inscrire")
        self._register_btn.setObjectName("signup_btn")
        self._register_btn.setFixedHeight(50)
        self._register_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._register_btn.clicked.connect(self._on_register_clicked)
        right_layout.addWidget(self._register_btn)

        right_layout.addSpacing(10)

        # Back-to-login link
        login_row = QHBoxLayout()
        login_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        login_hint = QLabel("Déjà un compte ?")
        login_hint.setStyleSheet("color: #555555; background: transparent; border: none;")
        login_row.addWidget(login_hint)

        self._login_link = QPushButton("Se connecter")
        self._login_link.setObjectName("login_link")
        self._login_link.setCursor(Qt.CursorShape.PointingHandCursor)
        self._login_link.setFlat(True)
        self._login_link.clicked.connect(self._on_login_clicked)
        login_row.addWidget(self._login_link)
        right_layout.addLayout(login_row)

        right_layout.addStretch()

        h_layout.addWidget(right_panel)

        self.setStyleSheet("""
            QLineEdit {
                border-radius: 24px;
                border: 1px solid #e0e0e0;
                background: #f8f9fc;
                padding-left: 25px;
                font-size: 14px;
                color: #000000;
            }
            QLineEdit:focus {
                border: 2px solid #93DC5C;
                background: white;
            }
            QPushButton#signup_btn {
                border-radius: 24px;
                background-color: #93DC5C;
                color: white;
                font-weight: bold;
                font-size: 16px;
                border: none;
            }
            QPushButton#signup_btn:hover {
                background-color: #7ab84d;
            }
            QPushButton#login_link {
                background: transparent;
                color: #4e732d;
                font-weight: bold;
                font-size: 14px;
                border: none;
                padding: 0px;
                text-decoration: underline;
            }
            QPushButton#login_link:hover {
                color: #93DC5C;
            }
        """)

    def _on_login_clicked(self) -> None:
        """Return to the login screen."""
        self.login_requested.emit()
        self.reject()

    def _on_register_clicked(self) -> None:
        """Validate inputs and register the new user."""
        nom = self._nom_input.text().strip()
        email = self._email_input.text().strip()
        password = self._password_input.text()
        confirm = self._confirm_input.text()

        if not all([nom, email, password, confirm]):
            self._error_label.setText("Veuillez remplir tous les champs.")
            return

        if password != confirm:
            self._error_label.setText("Les mots de passe ne correspondent pas.")
            return

        self._error_label.setText("")
        self._register_btn.setEnabled(False)
        self._register_btn.setText("Inscription en cours...")

        try:
            result = self._auth_ctrl.register(nom, email, password, ip="127.0.0.1")
            self.register_success.emit(result)
            self.accept()
        except ValueError as e:
            self._error_label.setText(str(e))
        except Exception as e:
            self._error_label.setText(f"Erreur: {str(e)}")
        finally:
            self._register_btn.setEnabled(True)
            self._register_btn.setText("S'inscrire")
