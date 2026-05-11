"""PySide6 widget for system administration."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QGroupBox,
    QGridLayout,
    QMessageBox,
)
from PySide6.QtCore import Qt

from controllers.admin_controller import AdminController


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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Title
        title = QLabel("⚙️ Administration Système")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        # Statistics Group
        stats_group = QGroupBox("Statistiques Système")
        stats_layout = QGridLayout(stats_group)
        
        self._lbl_total_users = QLabel("Utilisateurs: -")
        self._lbl_total_analyses = QLabel("Analyses: -")
        self._lbl_total_reports = QLabel("Rapports: -")
        self._lbl_total_data = QLabel("Données: - Mo")
        self._lbl_anomalies = QLabel("Anomalies (30j): -")

        stats_layout.addWidget(self._lbl_total_users, 0, 0)
        stats_layout.addWidget(self._lbl_total_analyses, 0, 1)
        stats_layout.addWidget(self._lbl_total_reports, 1, 0)
        stats_layout.addWidget(self._lbl_total_data, 1, 1)
        stats_layout.addWidget(self._lbl_anomalies, 2, 0)

        layout.addWidget(stats_group)

        # User Management Group
        user_group = QGroupBox("Gestion des Utilisateurs")
        user_layout = QVBoxLayout(user_group)

        btn_layout = QHBoxLayout()
        self._btn_refresh = QPushButton("🔄 Actualiser")
        self._btn_refresh.clicked.connect(self.refresh_data)
        btn_layout.addWidget(self._btn_refresh)
        btn_layout.addStretch()
        user_layout.addLayout(btn_layout)

        self._user_table = QTableWidget()
        self._user_table.setColumnCount(5)
        self._user_table.setHorizontalHeaderLabels(
            ["ID", "Nom", "Email", "Rôle", "Statut"]
        )
        self._user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        user_layout.addWidget(self._user_table)

        layout.addWidget(user_group)
        layout.addStretch()

    def refresh_data(self) -> None:
        """Fetch and display the latest system data."""
        try:
            # Stats
            stats = self._admin_ctrl.get_statistiques_systeme()
            self._lbl_total_users.setText(f"Utilisateurs: {stats['total_users']} ({stats['active_users']} actifs)")
            self._lbl_total_analyses.setText(f"Analyses: {stats['total_analyses']}")
            self._lbl_total_reports.setText(f"Rapports: {stats['total_reports']}")
            self._lbl_total_data.setText(f"Données: {stats['total_data_mo']} Mo")
            self._lbl_anomalies.setText(f"Anomalies (30j): {stats['anomalies_30j']}")

            # Users
            users = self._admin_ctrl.lister_utilisateurs()
            self._user_table.setRowCount(len(users))
            for i, user in enumerate(users):
                self._user_table.setItem(i, 0, QTableWidgetItem(str(user.id)))
                self._user_table.setItem(i, 1, QTableWidgetItem(user.nom))
                self._user_table.setItem(i, 2, QTableWidgetItem(user.email))
                self._user_table.setItem(i, 3, QTableWidgetItem(user.role))
                self._user_table.setItem(i, 4, QTableWidgetItem(user.statut))

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les données admin: {e}")
