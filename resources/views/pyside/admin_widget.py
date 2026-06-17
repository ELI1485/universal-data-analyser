"""PySide6 admin widget — Streamlit-matching design."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QMessageBox,
    QScrollArea,
    QTabWidget,
    QLineEdit,
    QComboBox,
    QFrame,
)
from PySide6.QtCore import Qt

from app.Http.Controllers.admin_controller import AdminController
from resources.views.pyside.style_widgets import MetricCard, SectionTitle, SubSectionTitle, Separator


class AdminWidget(QWidget):
    """Widget for system administrators to manage users and view stats."""

    def __init__(self, user_id: int, role: str) -> None:
        """Initialize the admin widget."""
        super().__init__()
        self._user_id = user_id
        self._role = role
        self._admin_ctrl = AdminController()

        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self) -> None:
        """Set up the admin UI components."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #f8f9fc; }")

        page = QWidget()
        page.setStyleSheet("background-color: #f8f9fc;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(12)

        # Title
        layout.addWidget(SectionTitle("Administration", "⚙️"))
        layout.addWidget(Separator())

        # Tabs
        self._tabs = QTabWidget()

        # Tab 1: System Stats
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setContentsMargins(15, 15, 15, 15)

        stats_layout.addWidget(SubSectionTitle("Statistiques systeme", "🏢"))
        
        self._kpi_layout = QHBoxLayout()
        self._kpi_layout.setSpacing(10)
        stats_layout.addLayout(self._kpi_layout)
        stats_layout.addStretch()

        self._tabs.addTab(stats_widget, "Tableau de bord")

        # Tab 2: Users
        users_widget = QWidget()
        users_layout = QVBoxLayout(users_widget)
        users_layout.setContentsMargins(15, 15, 15, 15)

        header_layout = QHBoxLayout()
        header_layout.addWidget(SubSectionTitle("Gestion des utilisateurs", "👥"))
        header_layout.addStretch()

        self._btn_refresh = QPushButton("🔄 Actualiser")
        self._btn_refresh.setStyleSheet("""
            QPushButton { background-color: #f0f2f6; color: #31333f; border-radius: 6px; padding: 6px 12px; font-weight: bold; border: 1px solid #e0e0e0; }
            QPushButton:hover { background-color: #e0e4eb; }
        """)
        self._btn_refresh.clicked.connect(self.refresh_data)
        header_layout.addWidget(self._btn_refresh)
        users_layout.addLayout(header_layout)

        self._user_table = QTableWidget()
        self._user_table.setColumnCount(5)
        self._user_table.setHorizontalHeaderLabels(
            ["Nom", "Email", "Role", "Statut", "Actions"]
        )
        self._user_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._user_table.setAlternatingRowColors(True)
        users_layout.addWidget(self._user_table)

        users_layout.addWidget(Separator())
        users_layout.addWidget(SubSectionTitle("Creer un utilisateur", "➕"))

        form_frame = QFrame()
        form_frame.setStyleSheet("QFrame { background: white; border-radius: 8px; border: 1px solid #e0e0e0; padding: 15px; }")
        form_layout = QVBoxLayout(form_frame)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Nom complet")
        form_layout.addWidget(self._name_input)

        self._email_input = QLineEdit()
        self._email_input.setPlaceholderText("Email")
        form_layout.addWidget(self._email_input)

        self._pass_input = QLineEdit()
        self._pass_input.setPlaceholderText("Mot de passe")
        self._pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addWidget(self._pass_input)

        self._role_combo = QComboBox()
        self._role_combo.addItems(["analyste", "admin"])
        form_layout.addWidget(self._role_combo)

        create_btn = QPushButton("Creer l'utilisateur")
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.clicked.connect(self._on_create_user)
        form_layout.addWidget(create_btn)

        users_layout.addWidget(form_frame)
        self._tabs.addTab(users_widget, "Utilisateurs")

        layout.addWidget(self._tabs)
        layout.addStretch()

        scroll.setWidget(page)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def refresh_data(self) -> None:
        """Fetch and display the latest system data."""
        try:
            # Stats
            stats = self._admin_ctrl.get_statistiques_systeme()
            self._clear_layout(self._kpi_layout)
            self._kpi_layout.addWidget(MetricCard("Utilisateurs totaux", str(stats["total_users"]), "👥"))
            self._kpi_layout.addWidget(MetricCard("Analyses effectuees", str(stats["total_analyses"]), "📈"))
            self._kpi_layout.addWidget(MetricCard("Rapports generes", str(stats["total_reports"]), "📄"))
            self._kpi_layout.addWidget(MetricCard("Volume de donnees", f"{stats['total_data_mo']:.1f} Mo", "💾"))

            # Users
            users = self._admin_ctrl.lister_utilisateurs()
            self._user_table.setRowCount(len(users))
            for i, user in enumerate(users):
                self._user_table.setItem(i, 0, QTableWidgetItem(user.nom))
                self._user_table.setItem(i, 1, QTableWidgetItem(user.email))
                self._user_table.setItem(i, 2, QTableWidgetItem(user.role))
                
                status_item = QTableWidgetItem(user.statut)
                if user.statut == "actif":
                    status_item.setForeground(Qt.GlobalColor.darkGreen)
                else:
                    status_item.setForeground(Qt.GlobalColor.darkRed)
                self._user_table.setItem(i, 3, status_item)

                # Actions layout
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(0, 0, 0, 0)

                deact_btn = QPushButton("⏸️")
                deact_btn.setToolTip("Désactiver")
                deact_btn.setFixedSize(30, 30)
                deact_btn.clicked.connect(lambda checked, uid=user.id: self._on_deactivate(uid))

                reset_btn = QPushButton("🔑")
                reset_btn.setToolTip("Réinitialiser mot de passe")
                reset_btn.setFixedSize(30, 30)
                reset_btn.clicked.connect(lambda checked, uid=user.id: self._on_reset(uid))

                del_btn = QPushButton("🗑️")
                del_btn.setToolTip("Supprimer")
                del_btn.setFixedSize(30, 30)
                del_btn.clicked.connect(lambda checked, uid=user.id: self._on_delete(uid))

                action_layout.addWidget(deact_btn)
                action_layout.addWidget(reset_btn)
                action_layout.addWidget(del_btn)
                action_layout.addStretch()

                self._user_table.setCellWidget(i, 4, action_widget)

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les données admin: {e}")

    def _on_deactivate(self, uid: int) -> None:
        try:
            self._admin_ctrl.desactiver_utilisateur(uid)
            QMessageBox.information(self, "Succès", "Utilisateur désactivé.")
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def _on_reset(self, uid: int) -> None:
        try:
            self._admin_ctrl.reinitialiser_mdp(uid, "NewPass123!")
            QMessageBox.information(self, "Succès", "Mot de passe réinitialisé: NewPass123!")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def _on_delete(self, uid: int) -> None:
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            "Supprimer cet utilisateur définitivement?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self._admin_ctrl.supprimer_utilisateur(uid)
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def _on_create_user(self) -> None:
        nom = self._name_input.text().strip()
        email = self._email_input.text().strip()
        password = self._pass_input.text()
        role = self._role_combo.currentText()

        if not all([nom, email, password]):
            QMessageBox.warning(self, "Attention", "Tous les champs sont obligatoires.")
            return

        try:
            self._admin_ctrl.creer_utilisateur(nom, email, password, role)
            QMessageBox.information(self, "Succès", f"Utilisateur '{nom}' créé.")
            self._name_input.clear()
            self._email_input.clear()
            self._pass_input.clear()
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def _clear_layout(self, layout):
        """Remove all widgets from a layout."""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
