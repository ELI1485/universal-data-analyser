# Universal Data Analyzer

A production-ready Python data analytics platform that imports Excel/CSV files, runs a full ETL pipeline, performs statistical analysis with anomaly detection, generates AI-powered insights via Gemini, and exports professional reports in PDF and Excel formats.

## Features

- **Data Import**: CSV, XLSX, XLS file ingestion with encoding detection
- **ETL Pipeline**: Automated extraction, validation, cleaning, and loading
- **Statistical Analysis**: Descriptive statistics, trend analysis, KPIs, K-means clustering
- **Anomaly Detection**: Z-Score, IQR, and Isolation Forest algorithms (parallel execution)
- **AI Insights**: Gemini API integration for intelligent French-language analytical summaries
- **Report Generation**: PDF (ReportLab) and Excel (openpyxl) with embedded charts
- **Dual Interface**: Streamlit web dashboard + PySide6 desktop application
- **Role-Based Access**: Admin and Analyste roles with JWT authentication
- **Audit Logging**: Complete audit trail for all operations
- **Scheduled Tasks**: APScheduler for background periodic tasks

---

## Architecture (5-Layer MVC)

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1 — VIEWS                                             │
│  Streamlit Pages + PySide6 Windows                           │
├─────────────────────────────────────────────────────────────┤
│  Layer 2 — CONTROLLERS                                       │
│  AuthController, UploadController, AnalyticsController,      │
│  ReportController, AdminController                           │
├─────────────────────────────────────────────────────────────┤
│  Layer 3 — SERVICES                                          │
│  ETLService, CleaningService, AnalyticsService,              │
│  AnomalyService, LLMService, ReportService,                  │
│  VisualizationService, AuditService, SchedulerService        │
├─────────────────────────────────────────────────────────────┤
│  Layer 4 — REPOSITORIES                                      │
│  DatasetRepository, AnomalyRepository, ReportRepository,     │
│  UserRepository, AuditRepository                             │
├─────────────────────────────────────────────────────────────┤
│  Layer 5 — MODELS (ORM)                                      │
│  Dataset, Anomaly, Report, User, AuditLog (SQLAlchemy)       │
├─────────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE                                              │
│  MySQL 8.0+ | Gemini API (external)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

- **Python** 3.11+
- **MySQL** 8.0+
- **Gemini API Key** (free at [aistudio.google.com](https://aistudio.google.com))

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/ELI1485/universal-data-analyser.git
cd universal-data-analyser
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env with your MySQL credentials and Gemini API key
```

### 5. Create the MySQL database

```sql
CREATE DATABASE universal_data_analyzer CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 6. Initialize the database (create tables + seed admin)

```bash
python database/init_db.py
```

---

## Running the Application

### Streamlit Web Dashboard (recommended)

```bash
streamlit run views/streamlit/app.py
```

Open http://localhost:8501 in your browser.

### PySide6 Desktop Application

```bash
python views/pyside/main_window.py
```

---

## Default Admin Credentials

| Field    | Value           |
|----------|-----------------|
| Email    | admin@uda.local |
| Password | Admin1234!      |
| Role     | admin           |

---

## Running Tests

```bash
# Run all tests with coverage
pytest --cov=. --cov-report=html

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run with verbose output
pytest -v
```

---

## Project Structure

```
universal-data-analyser/
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore rules
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── config/
│   ├── __init__.py
│   ├── settings.py                 # Environment config loader
│   └── logging_config.py           # Logging configuration
├── database/
│   ├── __init__.py
│   ├── base.py                     # SQLAlchemy declarative base
│   ├── connection.py               # Engine + session management
│   └── init_db.py                  # Table creation + admin seed
├── models/
│   ├── __init__.py
│   ├── user.py                     # User ORM model
│   ├── dataset.py                  # Dataset ORM model
│   ├── anomaly.py                  # Anomaly ORM model
│   ├── report.py                   # Report ORM model
│   └── audit_log.py                # AuditLog ORM model
├── repositories/
│   ├── __init__.py
│   ├── user_repository.py          # User CRUD
│   ├── dataset_repository.py       # Dataset CRUD
│   ├── anomaly_repository.py       # Anomaly CRUD
│   ├── report_repository.py        # Report CRUD
│   └── audit_repository.py         # Audit log CRUD
├── services/
│   ├── __init__.py
│   ├── auth_service.py             # JWT + bcrypt authentication
│   ├── audit_service.py            # Audit logging (DB + file)
│   ├── llm_service.py              # Gemini AI integration
│   ├── scheduler_service.py        # APScheduler background tasks
│   ├── etl/
│   │   ├── __init__.py
│   │   ├── ingestion_service.py    # File reading (CSV/Excel)
│   │   ├── validation_service.py   # Data quality validation
│   │   ├── cleaning_service.py     # Dedup, null fill, normalize
│   │   └── etl_service.py          # Pipeline orchestrator
│   ├── analytics/
│   │   ├── __init__.py
│   │   ├── descriptive_statistics.py
│   │   ├── trend_analysis.py
│   │   ├── kpi_engine.py
│   │   └── analytics_service.py    # Analytics orchestrator
│   ├── anomaly/
│   │   ├── __init__.py
│   │   ├── zscore_detector.py      # Z-Score detection
│   │   ├── iqr_detector.py         # IQR detection
│   │   ├── isolation_detector.py   # Isolation Forest
│   │   └── anomaly_service.py      # Parallel orchestrator
│   ├── reporting/
│   │   ├── __init__.py
│   │   ├── pdf_generator.py        # ReportLab PDF generation
│   │   ├── excel_generator.py      # openpyxl Excel generation
│   │   └── report_service.py       # Report orchestrator
│   └── visualization/
│       ├── __init__.py
│       └── visualization_service.py # Plotly + Matplotlib charts
├── controllers/
│   ├── __init__.py
│   ├── auth_controller.py          # Login/logout/token
│   ├── upload_controller.py        # File import + dataset mgmt
│   ├── analytics_controller.py     # Run/retrieve analyses
│   ├── report_controller.py        # Generate/list/download reports
│   └── admin_controller.py         # User mgmt + system stats
├── views/
│   ├── streamlit/
│   │   ├── app.py                  # Main entry (routing)
│   │   ├── login_page.py
│   │   ├── dashboard_page.py
│   │   ├── upload_page.py
│   │   ├── analytics_page.py
│   │   ├── report_page.py
│   │   └── admin_page.py
│   └── pyside/
│       ├── main_window.py          # Desktop entry point
│       ├── login_dialog.py
│       ├── upload_widget.py
│       ├── analytics_widget.py
│       └── report_widget.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures
│   ├── unit/
│   │   ├── test_auth_service.py
│   │   ├── test_cleaning_service.py
│   │   ├── test_analytics_service.py
│   │   └── test_anomaly_service.py
│   └── integration/
│       └── test_etl_pipeline.py
├── logs/                           # Created at runtime (gitignored)
└── exports/                        # Created at runtime (gitignored)
```

---

## Key Design Decisions

| Concern | Solution |
|---------|----------|
| Authentication | JWT tokens + bcrypt password hashing |
| Authorization | Role-based (admin/analyste) at controller level |
| Database | MySQL 8.0 via SQLAlchemy ORM |
| ETL | Pandas-based with encoding detection |
| Anomaly Detection | 3 algorithms in parallel (ThreadPoolExecutor) |
| AI/LLM | Google Gemini with graceful degradation |
| Reporting | ReportLab (PDF) + openpyxl (Excel) |
| Charts | Plotly (interactive/Streamlit) + Matplotlib (PDF) |
| Scheduling | APScheduler background tasks |
| Logging | Rotating file handlers (app, error, audit) |

---

## Environment Variables

See `.env.example` for all configuration options. Key variables:

| Variable | Description |
|----------|-------------|
| `DB_HOST` | MySQL host |
| `DB_NAME` | Database name |
| `GEMINI_API_KEY` | Google Gemini API key |
| `JWT_SECRET_KEY` | Secret for JWT signing |
| `MAX_FILE_SIZE_MB` | Maximum upload size |
| `MAX_LOGIN_ATTEMPTS` | Before account suspension |

---

## License

MIT License
