"""PySide6 main window for the desktop application.

Run with: python views/pyside/main_window.py
"""

import sys
from pathlib import Path

# Add project root to path
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QMessageBox,
    QMenuBar,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from config.logging_config import setup_logging
from config.settings import LOG_DIR, LOG_LEVEL
from resources.views.pyside.login_dialog import LoginDialog
from resources.views.pyside.upload_widget import UploadWidget
from resources.views.pyside.analytics_widget import AnalyticsWidget
from resources.views.pyside.report_widget import ReportWidget
from resources.views.pyside.admin_widget import AdminWidget


class MainWindow(QMainWindow):
    """Main application window for the PySide6 desktop interface.

    Provides navigation, authentication, and page switching.
    """

    def __init__(self) -> None:
        """Initialize the main window."""
        super().__init__()
        self._token = None
        self._user_id = None
        self._role = None
        self._nom = None

        self.setWindowTitle("Universal Data Analyzer")
        self.setMinimumSize(1200, 800)

        setup_logging(log_dir=LOG_DIR, log_level=LOG_LEVEL)

        self._setup_ui()
        self._show_login()

    def _setup_ui(self) -> None:
        """Set up the main window UI components."""
        # Menu bar
        self._create_menu_bar()

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left sidebar
        self._sidebar = QWidget()
        self._sidebar.setFixedWidth(200)
        self._sidebar.setStyleSheet(
            "QWidget { background-color: #1a237e; } "
            "QPushButton { color: white; text-align: left; padding: 12px; "
            "border: none; font-size: 13px; } "
            "QPushButton:hover { background-color: #283593; } "
            "QLabel { color: white; padding: 8px; }"
        )
        sidebar_layout = QVBoxLayout(self._sidebar)
        sidebar_layout.setContentsMargins(0, 10, 0, 10)

        self._user_label = QLabel("")
        self._user_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        sidebar_layout.addWidget(self._user_label)

        self._role_label = QLabel("")
        sidebar_layout.addWidget(self._role_label)

        sidebar_layout.addSpacing(20)

        self._nav_dashboard = QPushButton("🏠 Tableau de bord")
        self._nav_dashboard.clicked.connect(lambda: self._switch_page(0))
        sidebar_layout.addWidget(self._nav_dashboard)

        self._nav_upload = QPushButton("📁 Import")
        self._nav_upload.clicked.connect(lambda: self._switch_page(1))
        sidebar_layout.addWidget(self._nav_upload)

        self._nav_analytics = QPushButton("📈 Analyses")
        self._nav_analytics.clicked.connect(lambda: self._switch_page(2))
        sidebar_layout.addWidget(self._nav_analytics)

        self._nav_reports = QPushButton("📄 Rapports")
        self._nav_reports.clicked.connect(lambda: self._switch_page(3))
        sidebar_layout.addWidget(self._nav_reports)

        self._nav_admin = QPushButton("⚙️ Administration")
        self._nav_admin.clicked.connect(lambda: self._switch_page(4))
        self._nav_admin.setVisible(False)
        sidebar_layout.addWidget(self._nav_admin)

        sidebar_layout.addStretch()

        self._logout_btn = QPushButton("🚪 Déconnexion")
        self._logout_btn.clicked.connect(self._on_logout)
        sidebar_layout.addWidget(self._logout_btn)

        main_layout.addWidget(self._sidebar)

        # Stacked widget for pages
        self._stack = QStackedWidget()
        main_layout.addWidget(self._stack)

        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Non connecté")

        # Initially hide the main content
        self._sidebar.setVisible(False)

    def _create_menu_bar(self) -> None:
        """Create the application menu bar."""
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("Fichier")
        logout_action = QAction("Déconnexion", self)
        logout_action.triggered.connect(self._on_logout)
        file_menu.addAction(logout_action)
        quit_action = QAction("Quitter", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Analyses menu
        analyses_menu = menu_bar.addMenu("Analyses")
        run_action = QAction("Lancer une analyse", self)
        run_action.triggered.connect(lambda: self._switch_page(2))
        analyses_menu.addAction(run_action)

        # Reports menu
        reports_menu = menu_bar.addMenu("Rapports")
        gen_action = QAction("Générer un rapport", self)
        gen_action.triggered.connect(lambda: self._switch_page(3))
        reports_menu.addAction(gen_action)

        # Help menu
        help_menu = menu_bar.addMenu("Aide")
        about_action = QAction("À propos", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _show_login(self) -> None:
        """Show the login dialog."""
        dialog = LoginDialog(self)
        dialog.login_success.connect(self._on_login_success)
        result = dialog.exec()

        if result != LoginDialog.DialogCode.Accepted:
            sys.exit(0)

    def _on_login_success(self, result: dict) -> None:
        """Handle successful login.

        Args:
            result: Login result dict with token, user_id, role, nom.
        """
        self._token = result["token"]
        self._user_id = result["user_id"]
        self._role = result["role"]
        self._nom = result["nom"]

        self._user_label.setText(f"  {self._nom}")
        self._role_label.setText(f"  Rôle: {self._role}")
        self._status_bar.showMessage(
            f"Connecté: {self._nom} ({self._role})"
        )

        self._nav_admin.setVisible(self._role == "admin")

        self._sidebar.setVisible(True)
        self._setup_pages()
        self._switch_page(0)

    def _setup_pages(self) -> None:
        """Set up the stacked widget pages after login."""
        # Clear existing pages
        while self._stack.count() > 0:
            widget = self._stack.widget(0)
            self._stack.removeWidget(widget)
            widget.deleteLater()

        # Page 0: Dashboard
        dashboard = QWidget()
        dash_layout = QVBoxLayout(dashboard)
        dash_layout.addWidget(QLabel(f"🏠 Bienvenue, {self._nom}!"))
        dash_layout.addWidget(QLabel("Utilisez le menu de gauche pour naviguer."))
        dash_layout.addStretch()
        self._stack.addWidget(dashboard)

        # Page 1: Upload
        upload_widget = UploadWidget(self._user_id, self._role)
        self._stack.addWidget(upload_widget)

        # Page 2: Analytics
        analytics_widget = AnalyticsWidget(self._user_id, self._role)
        self._stack.addWidget(analytics_widget)

        # Page 3: Reports
        report_widget = ReportWidget(self._user_id, self._role)
        self._stack.addWidget(report_widget)

        # Page 4: Admin
        if self._role == "admin":
            admin_widget = AdminWidget(self._user_id, self._role)
            self._stack.addWidget(admin_widget)

    def _switch_page(self, index: int) -> None:
        """Switch the visible page in the stacked widget.

        Args:
            index: Page index to show.
        """
        if index < self._stack.count():
            self._stack.setCurrentIndex(index)

    def _on_logout(self) -> None:
        """Handle logout."""
        from app.Http.Controllers.auth_controller import AuthController
        auth_ctrl = AuthController()
        try:
            auth_ctrl.logout(self._token)
        except Exception:
            pass

        self._token = None
        self._user_id = None
        self._role = None
        self._nom = None

        self._sidebar.setVisible(False)
        self._status_bar.showMessage("Déconnecté")
        self._show_login()

    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "À propos",
            "Universal Data Analyzer v1.0\n\n"
            "Plateforme d'analyse de données avec:\n"
            "- Pipeline ETL (CSV/Excel)\n"
            "- Statistiques descriptives\n"
            "- Détection d'anomalies\n"
            "- Insights IA (Gemini)\n"
            "- Rapports PDF/Excel\n\n"
            "Architecture MVC 5 couches",
        )

    def closeEvent(self, event) -> None:
        """Handle window close event with confirmation."""
        reply = QMessageBox.question(
            self,
            "Quitter",
            "Voulez-vous vraiment quitter l'application?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()


def main() -> None:
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Universal Data Analyzer")
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
