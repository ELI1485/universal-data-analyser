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
    QScrollArea,
    QFrame,
    QGridLayout,
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
from resources.views.pyside.style_widgets import MetricCard, SectionTitle, SubSectionTitle, Separator


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
        self._sidebar.setFixedWidth(240)
        self._sidebar.setStyleSheet("""
            QWidget { background-color: #80C64A; }
            QPushButton { 
                background-color: transparent; 
                color: #ffffff; 
                text-align: left; 
                padding: 12px 15px; 
                border: none; 
                font-size: 14px; 
                border-radius: 8px; 
                margin: 2px 10px; 
                font-weight: normal; 
            }
            QPushButton:hover { 
                background-color: rgba(255, 255, 255, 0.2); 
                color: #ffffff; 
                font-weight: bold; 
            }
            QLabel { color: #ffffff; padding: 8px; background-color: transparent; }
        """)
        sidebar_layout = QVBoxLayout(self._sidebar)
        sidebar_layout.setContentsMargins(0, 10, 0, 10)

        # Logo area
        logo_frame = QFrame()
        logo_frame.setFixedHeight(110)
        logo_frame.setStyleSheet("background-color: transparent; border: none;")
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_icon = QLabel("📊")
        logo_icon.setStyleSheet("font-size: 40px; background: transparent; border: none;")
        logo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_icon)

        logo_text = QLabel("UDA")
        logo_text.setStyleSheet("font-size: 18px; font-weight: bold; color: white; background: transparent; border: none;")
        logo_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_text)

        sidebar_layout.addWidget(logo_frame)

        # User info
        self._user_label = QLabel("")
        self._user_label.setStyleSheet("font-weight: bold; font-size: 14px; color: white; background: transparent;")
        self._user_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(self._user_label)

        self._role_label = QLabel("")
        self._role_label.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.8); background: transparent;")
        self._role_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(self._role_label)

        sidebar_layout.addSpacing(20)

        self._nav_dashboard = QPushButton("🏠  Tableau de bord")
        self._nav_dashboard.clicked.connect(lambda: self._switch_page(0))
        sidebar_layout.addWidget(self._nav_dashboard)

        self._nav_upload = QPushButton("📁  Importer des donnees")
        self._nav_upload.clicked.connect(lambda: self._switch_page(1))
        sidebar_layout.addWidget(self._nav_upload)

        self._nav_analytics = QPushButton("📈  Analyses")
        self._nav_analytics.clicked.connect(lambda: self._switch_page(2))
        sidebar_layout.addWidget(self._nav_analytics)

        self._nav_reports = QPushButton("📄  Rapports")
        self._nav_reports.clicked.connect(lambda: self._switch_page(3))
        sidebar_layout.addWidget(self._nav_reports)

        self._nav_admin = QPushButton("⚙️  Administration")
        self._nav_admin.clicked.connect(lambda: self._switch_page(4))
        self._nav_admin.setVisible(False)
        sidebar_layout.addWidget(self._nav_admin)

        sidebar_layout.addStretch()

        self._logout_btn = QPushButton("🚪  Deconnexion")
        self._logout_btn.clicked.connect(self._on_logout)
        sidebar_layout.addWidget(self._logout_btn)

        main_layout.addWidget(self._sidebar)

        # Stacked widget for pages
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("QStackedWidget { background-color: #f8f9fc; }")
        main_layout.addWidget(self._stack)

        # Status bar
        self._status_bar = QStatusBar()
        self._status_bar.setStyleSheet("QStatusBar { background-color: #ffffff; color: #31333f; border-top: 1px solid #e0e0e0; }")
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

        self._user_label.setText(self._nom)
        self._role_label.setText(self._role.capitalize())
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
        dashboard = self._create_dashboard_page()
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

    def _create_dashboard_page(self) -> QWidget:
        """Create the dashboard page matching the Streamlit dashboard."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #f8f9fc; }")

        page = QWidget()
        page.setStyleSheet("background-color: #f8f9fc;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        # Title
        layout.addWidget(SectionTitle("Tableau de bord", "🏠"))

        welcome = QLabel(f"Bienvenue, <b>{self._nom}</b>! Voici un resume de votre activite.")
        welcome.setStyleSheet("font-size: 14px; color: #555; background: transparent; border: none;")
        layout.addWidget(welcome)

        layout.addWidget(Separator())

        # Metric cards row
        try:
            from app.Http.Controllers.upload_controller import UploadController
            from app.Http.Controllers.report_controller import ReportController
            from app.Repositories.anomaly_repository import AnomalyRepository

            upload_ctrl = UploadController()
            report_ctrl = ReportController()
            anom_repo = AnomalyRepository()

            datasets = upload_ctrl.lister_datasets(self._user_id, self._role)
            reports = report_ctrl.lister_rapports(self._user_id, self._role)
            total_anomalies = anom_repo.count_recent(days=30)
            analyses_count = sum(1 for d in datasets if d.statut == "traite")

            cards_layout = QHBoxLayout()
            cards_layout.setSpacing(15)
            cards_layout.addWidget(MetricCard("Datasets importes", str(len(datasets)), "📊"))
            cards_layout.addWidget(MetricCard("Analyses effectuees", str(analyses_count), "📈"))
            cards_layout.addWidget(MetricCard("Rapports generes", str(len(reports)), "📄"))
            cards_layout.addWidget(MetricCard("Anomalies (30j)", str(total_anomalies), "⚠️"))
            layout.addLayout(cards_layout)
        except Exception:
            err = QLabel("Erreur lors du chargement des metriques.")
            err.setStyleSheet("color: #f59e0b; background: transparent; border: none;")
            layout.addWidget(err)
            datasets = []
            reports = []

        layout.addWidget(Separator())

        # Data Quality Section
        if datasets:
            layout.addWidget(SubSectionTitle("Qualite des donnees", "📊"))
            self._add_quality_gauges(layout, datasets)
            layout.addWidget(Separator())

        # System Stats (Admin only)
        if self._role == "admin":
            layout.addWidget(SubSectionTitle("Statistiques systeme", "🏢"))
            try:
                from app.Http.Controllers.admin_controller import AdminController
                admin_ctrl = AdminController()
                sys_stats = admin_ctrl.get_statistiques_systeme()

                admin_cards = QHBoxLayout()
                admin_cards.setSpacing(15)
                admin_cards.addWidget(MetricCard("Utilisateurs actifs", str(sys_stats["active_users"]), "👥"))
                admin_cards.addWidget(MetricCard("Volume total", f"{sys_stats['total_data_mo']:.1f} Mo", "💾"))
                admin_cards.addWidget(MetricCard("Total datasets", str(sys_stats["total_datasets"]), "🗄️"))
                admin_cards.addWidget(MetricCard("Total rapports", str(sys_stats["total_reports"]), "📋"))
                layout.addLayout(admin_cards)
            except Exception:
                pass
            layout.addWidget(Separator())

        # Activity Timeline
        layout.addWidget(SubSectionTitle("Activite recente", "🕐"))
        self._add_activity_timeline(layout)
        layout.addWidget(Separator())

        # Quick Actions
        layout.addWidget(SubSectionTitle("Actions rapides", "⚡"))
        self._add_quick_actions(layout)

        layout.addStretch()
        scroll.setWidget(page)
        return scroll

    def _add_quality_gauges(self, layout: QVBoxLayout, datasets) -> None:
        """Add data quality gauge charts using matplotlib."""
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
            import numpy as np

            recent = sorted(datasets, key=lambda d: d.cree_le or "", reverse=True)[:3]

            gauges_layout = QHBoxLayout()
            gauges_layout.setSpacing(15)

            for ds in recent:
                quality = 95 if ds.statut == "traite" else 70 if ds.statut == "en_traitement" else 50

                fig, ax = plt.subplots(figsize=(2.5, 2), subplot_kw={"projection": "polar"})
                fig.patch.set_facecolor("#f8f9fc")

                # Create gauge
                theta = np.linspace(0, np.pi, 100)
                ax.set_theta_zero_location("W")
                ax.set_theta_direction(-1)

                # Background arc
                ax.barh(1, np.pi, height=0.3, left=0, color="#e8e8e8", alpha=0.5)
                # Value arc
                value_angle = np.pi * quality / 100
                color = "#93DC5C" if quality >= 75 else "#f59e0b" if quality >= 50 else "#ef4444"
                ax.barh(1, value_angle, height=0.3, left=0, color=color)

                ax.set_ylim(0, 2)
                ax.set_xlim(0, np.pi)
                ax.axis("off")

                # Center text
                ax.text(np.pi / 2, 0.5, f"{quality}%", ha="center", va="center",
                        fontsize=18, fontweight="bold", color="#31333f",
                        transform=ax.transAxes)

                ax.set_title(ds.nom[:20], fontsize=10, color="#31333f", pad=5)

                canvas = FigureCanvas(fig)
                canvas.setFixedHeight(160)
                canvas.setStyleSheet("background-color: #f8f9fc; border: none;")

                card = QFrame()
                card.setStyleSheet("""
                    QFrame {
                        background-color: white;
                        border-radius: 12px;
                        border: 1px solid #e8e8e8;
                    }
                """)
                card_layout = QVBoxLayout(card)
                card_layout.setContentsMargins(10, 10, 10, 10)
                card_layout.addWidget(canvas)

                info = QLabel(f"{ds.nb_lignes} lignes - {ds.nb_colonnes} colonnes - {ds.taille_mo:.1f} Mo")
                info.setStyleSheet("font-size: 11px; color: #888; background: transparent; border: none;")
                info.setAlignment(Qt.AlignmentFlag.AlignCenter)
                card_layout.addWidget(info)

                gauges_layout.addWidget(card)
                plt.close(fig)

            layout.addLayout(gauges_layout)

        except Exception:
            layout.addWidget(QLabel("Impossible de charger les graphiques de qualite."))

    def _add_activity_timeline(self, layout: QVBoxLayout) -> None:
        """Add the activity timeline from audit logs."""
        try:
            from app.Repositories.audit_repository import AuditRepository
            audit_repo = AuditRepository()

            if self._role == "admin":
                logs = audit_repo.find_recent(limit=8)
            else:
                logs = audit_repo.find_by_user(self._user_id)[:8]

            if not logs:
                no_activity = QLabel("Aucune activite recente.")
                no_activity.setStyleSheet("color: #888; font-style: italic; background: transparent; border: none;")
                layout.addWidget(no_activity)
                return

            for log in logs:
                item_frame = QFrame()
                item_frame.setStyleSheet("""
                    QFrame {
                        border-left: 3px solid #93DC5C;
                        padding-left: 15px;
                        margin-left: 10px;
                        background: transparent;
                        border-top: none; border-right: none; border-bottom: none;
                        border-radius: 0;
                    }
                """)
                item_layout = QHBoxLayout(item_frame)
                item_layout.setContentsMargins(15, 8, 10, 8)

                # Dot
                dot = QLabel("●")
                dot_color = "#22c55e" if log.statut == "succes" else "#ef4444"
                dot.setStyleSheet(f"color: {dot_color}; font-size: 10px; background: transparent; border: none;")
                dot.setFixedWidth(15)
                item_layout.addWidget(dot)

                # Text
                text_layout = QVBoxLayout()
                action_label = QLabel(log.action)
                action_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #31333f; background: transparent; border: none;")
                text_layout.addWidget(action_label)

                timestamp = log.horodatage.strftime("%d/%m/%Y %H:%M") if log.horodatage else "N/A"
                message = (log.message[:60] + "...") if log.message and len(log.message) > 60 else (log.message or "")
                meta = QLabel(f"{log.entite} - {timestamp}{f' - {message}' if message else ''}")
                meta.setStyleSheet("font-size: 11px; color: #94a3b8; background: transparent; border: none;")
                text_layout.addWidget(meta)

                item_layout.addLayout(text_layout)
                item_layout.addStretch()

                layout.addWidget(item_frame)

        except Exception:
            no_activity = QLabel("Activite non disponible.")
            no_activity.setStyleSheet("color: #888; background: transparent; border: none;")
            layout.addWidget(no_activity)

    def _add_quick_actions(self, layout: QVBoxLayout) -> None:
        """Add quick action cards matching Streamlit's design."""
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(15)

        actions = [
            ("📁", "Importer", "CSV, Excel, XLS", 1),
            ("📊", "Analyser", "Stats, anomalies, IA", 2),
            ("📄", "Rapports", "PDF et Excel", 3),
        ]

        for icon, title, desc, page_idx in actions:
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 12px;
                    border: 1px solid #e8e8e8;
                    padding: 20px;
                }
                QFrame:hover {
                    border: 1px solid #93DC5C;
                }
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.setSpacing(8)

            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet("font-size: 32px; background: transparent; border: none;")
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(icon_lbl)

            title_lbl = QLabel(title)
            title_lbl.setStyleSheet("font-weight: bold; font-size: 15px; color: #31333f; background: transparent; border: none;")
            title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(title_lbl)

            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet("font-size: 12px; color: #94a3b8; background: transparent; border: none;")
            desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(desc_lbl)

            btn = QPushButton(f"Ouvrir {title.lower()}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #93DC5C; color: white; border-radius: 8px;
                    padding: 8px 20px; font-weight: bold; border: none;
                }
                QPushButton:hover { background-color: #7ab84d; }
            """)
            btn.clicked.connect(lambda checked, idx=page_idx: self._switch_page(idx))
            card_layout.addWidget(btn)

            actions_layout.addWidget(card)

        layout.addLayout(actions_layout)

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
    
    # Global StyleSheet to enforce Light Mode and Streamlit aesthetics
    app.setStyleSheet("""
        QWidget { background-color: #ffffff; color: #31333f; font-family: 'Segoe UI', Arial, sans-serif; }
        QTableWidget, QTableView { background-color: #ffffff; alternate-background-color: #f8f9fc; color: #31333f; gridline-color: #e0e0e0; border: 1px solid #e0e0e0; }
        QHeaderView::section { background-color: #f0f2f6; color: #31333f; font-weight: bold; border: 1px solid #e0e0e0; padding: 6px; }
        QLineEdit, QTextEdit { background-color: #ffffff; color: #31333f; border: 1px solid #e0e0e0; border-radius: 4px; padding: 6px; }
        QComboBox { background-color: #ffffff; color: #31333f; border: 1px solid #e0e0e0; border-radius: 4px; padding: 6px; }
        QComboBox QAbstractItemView { background-color: #ffffff; color: #31333f; selection-background-color: #93DC5C; }
        QComboBox::drop-down { border: none; }
        QPushButton { background-color: #93DC5C; color: white; border-radius: 6px; padding: 8px 16px; font-weight: bold; border: none; }
        QPushButton:hover { background-color: #7ab84d; }
        QPushButton:disabled { background-color: #d0d0d0; color: #888888; }
        QTabWidget::pane { border: 1px solid #e0e0e0; background: white; border-radius: 4px; }
        QTabBar::tab { background: #f0f2f6; color: #31333f; padding: 8px 20px; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; }
        QTabBar::tab:selected { background: white; font-weight: bold; border-bottom: 2px solid #93DC5C; }
        QTabBar::tab:hover { background: #e0e4eb; }
        QProgressBar { border: 1px solid #e0e0e0; border-radius: 6px; text-align: center; background: #f0f2f6; }
        QProgressBar::chunk { background-color: #93DC5C; border-radius: 6px; }
        QScrollBar:vertical { border: none; background: #f0f2f6; width: 10px; }
        QScrollBar::handle:vertical { background: #c0c0c0; min-height: 20px; border-radius: 5px; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { border: none; background: none; }
        QGroupBox { border: 1px solid #e0e0e0; border-radius: 8px; margin-top: 10px; padding-top: 15px; background: white; }
        QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 5px; color: #31333f; font-weight: bold; }
        QRadioButton { color: #31333f; background: transparent; }
        QCheckBox { color: #31333f; background: transparent; }
        QMenuBar { background-color: #ffffff; color: #31333f; border-bottom: 1px solid #e0e0e0; }
        QMenuBar::item:selected { background-color: #93DC5C; color: white; border-radius: 4px; }
        QMenu { background-color: #ffffff; color: #31333f; border: 1px solid #e0e0e0; }
        QMenu::item:selected { background-color: #93DC5C; color: white; }
        QMessageBox { background-color: #ffffff; }
    """)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
