"""PySide6 login dialog for user authentication."""

import sys
from pathlib import Path

_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from PySide6.QtWidgets import (  # noqa: E402
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
    QFrame,
    QCheckBox,
)
from PySide6.QtCore import Signal, Qt, QPoint  # noqa: E402

from app.Http.Controllers.auth_controller import AuthController  # noqa: E402


class LoginDialog(QDialog):
    """Modern Login dialog for PySide6 desktop application.

    Emits login_success signal with token and role on successful authentication.
    """

    login_success = Signal(dict)
    register_requested = Signal()

    def __init__(self, parent=None) -> None:
        """Initialize the login dialog.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self._auth_ctrl = AuthController()
        
        # Variables for custom dragging
        self._drag_pos = QPoint()
        
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the dialog UI components."""
        # Window settings
        self.setWindowTitle("Universal Data Analyzer — Connexion")
        self.setFixedSize(960, 520)
        self.setWindowFlags(Qt.WindowType.Dialog)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Container frame (for rounded corners and shadow simulation)
        container = QFrame(self)
        container.setObjectName("MainContainer")
        container.setStyleSheet(
            "#MainContainer {"
            "  background-color: white;"
            "  border-radius: 20px;"
            "}"
        )
        main_layout.addWidget(container)
        
        # Horizontal layout inside container
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)
        
        # --- LEFT PANEL ---
        left_panel = QWidget()
        left_panel.setFixedWidth(480)
        left_layout = QGridLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Background image
        bg_label = QLabel()
        bg_label.setScaledContents(True)
        # Use safe local gradient instead of relying on external Unsplash image which can hang the UI
        bg_label.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #93DC5C, stop:1 #4e732d); border-top-left-radius: 20px; border-bottom-left-radius: 20px;")
        
        left_layout.addWidget(bg_label, 0, 0)
        
        # 2. Dark overlay (to make the image darker like in Streamlit)
        overlay = QFrame()
        overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.3); border-top-left-radius: 20px; border-bottom-left-radius: 20px;")
        left_layout.addWidget(overlay, 0, 0)
        
        # 3. Logo box
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
        
        icon_label = QLabel("\u25a6")
        icon_label.setStyleSheet("font-size: 60px; background: transparent; color: white;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(icon_label)
        
        brand_label = QLabel("UDA Portal")
        brand_label.setStyleSheet("color: white; font-weight: bold; font-size: 20px; background: transparent;")
        brand_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(brand_label)
        
        left_layout.addWidget(logo_box, 0, 0, Qt.AlignmentFlag.AlignCenter)
        h_layout.addWidget(left_panel)
        
        # --- RIGHT PANEL ---
        right_panel = QFrame()
        # Give the panel an explicit white background so its dark labels never
        # render white-on-white when global stylesheets change.
        right_panel.setObjectName("RightPanel")
        right_panel.setStyleSheet(
            "#RightPanel { background-color: white;"
            " border-top-right-radius: 20px; border-bottom-right-radius: 20px; }"
        )
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(50, 20, 50, 40)
        
        right_layout.addStretch()
        
        # Title
        title_label = QLabel("Plateforme eServices")
        title_label.setStyleSheet("font-size: 24px; color: #2c3e50; font-weight: 300; margin-bottom: 20px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(title_label)
        
        # Email field
        self._email_input = QLineEdit()
        self._email_input.setPlaceholderText("Ex: admin@uda.local")
        self._email_input.setFixedHeight(50)
        right_layout.addWidget(self._email_input)
        
        right_layout.addSpacing(10)
        
        # Password field
        self._password_input = QLineEdit()
        self._password_input.setPlaceholderText("••••••••••••")
        self._password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_input.setFixedHeight(50)
        self._password_input.returnPressed.connect(self._on_login_clicked)
        right_layout.addWidget(self._password_input)
        
        right_layout.addSpacing(10)
        
        # Remember me
        self._remember_cb = QCheckBox("Se rappeler de moi")
        self._remember_cb.setStyleSheet("color: #666;")
        right_layout.addWidget(self._remember_cb)
        
        right_layout.addSpacing(15)
        
        # Error label
        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.setWordWrap(True)
        right_layout.addWidget(self._error_label)
        
        # Login button
        self._login_btn = QPushButton("Se connecter")
        self._login_btn.setFixedHeight(50)
        self._login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._login_btn.clicked.connect(self._on_login_clicked)
        right_layout.addWidget(self._login_btn)

        right_layout.addSpacing(12)

        # Register prompt (mirrors Streamlit's "Don't have an account? Create one")
        register_row = QHBoxLayout()
        register_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        register_hint = QLabel("Vous n'avez pas de compte ?")
        register_hint.setStyleSheet("color: #555555; background: transparent; border: none;")
        register_row.addWidget(register_hint)

        self._register_btn = QPushButton("Créer un compte")
        self._register_btn.setObjectName("register_btn")
        self._register_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._register_btn.setFlat(True)
        self._register_btn.clicked.connect(self._on_register_clicked)
        register_row.addWidget(self._register_btn)
        right_layout.addLayout(register_row)

        right_layout.addStretch()
        
        # Footer
        footer = QLabel("Mot de passe oublié ?    |    Questions ?\n\nCopyright © 2026 - Tous droits réservés")
        footer.setStyleSheet("color: #a0a0a0; font-size: 12px;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(footer)
        
        h_layout.addWidget(right_panel)
        
        # Apply global QSS for right panel inputs
        self.setStyleSheet("""
            QLineEdit {
                border-radius: 25px;
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
            QPushButton#login_btn {
                border-radius: 25px;
                background-color: #93DC5C;
                color: white;
                font-weight: bold;
                font-size: 16px;
                border: none;
            }
            QPushButton#login_btn:hover {
                background-color: #7ab84d;
            }
            QPushButton#register_btn {
                background: transparent;
                color: #4e732d;
                font-weight: bold;
                font-size: 14px;
                border: none;
                padding: 0px;
                text-decoration: underline;
            }
            QPushButton#register_btn:hover {
                color: #93DC5C;
            }
        """)
        self._login_btn.setObjectName("login_btn")

    def _on_register_clicked(self) -> None:
        """Handle the "Créer un compte" link click.

        Emits ``register_requested`` so the main window can open the
        registration dialog, then closes the login dialog.
        """
        self.register_requested.emit()
        # Close the login dialog with a "rejected" code; the main window
        # listens to register_requested to decide what to show next.
        self.reject()

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
