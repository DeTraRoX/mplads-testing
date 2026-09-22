# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-09-22

### Added
- 🗺️ Interactive Geospatial Intelligence Hub with Leaflet.js integration
- 🇮🇳 Enhanced Dashboard with MoSPI/GOI government branding
- 📊 CSV Export functionality for forensic audit reports
- 🌐 Bilingual support (English/Hindi) with i18n
- 🔍 5-factor AI/ML detection engine:
  - Isolation Forest for cost anomaly detection
  - Sentence-BERT (all-MiniLM-L6-v2) for duplicate detection
  - Local Outlier Factor for density-based anomalies
  - Haversine formula for GPS deviation calculation
  - Weighted composite risk scoring
- 🛡️ Hash-chained audit logs for tamper-evidence
- 👥 Role-based access control (Admin, Officer, Auditor)
- 📸 Evidence photo management with SHA-256 verification
- 🤖 Ollama LLM integration with intelligent fallback
- 📱 Responsive design with Tailwind CSS
- 🚀 Production-ready deployment configuration

### Database
- Seeded with 1,051 realistic MPLADS projects
- 195+ flagged anomalies across multiple categories
- Worked example: MP-2024-8842 with complete case history
- 7 states, 36 districts, 15 contractors

### Technical
- FastAPI backend with async/await
- React 18 with Vite build system
- SQLite with PostgreSQL migration path
- Comprehensive API documentation with OpenAPI/Swagger
- Automated startup script for macOS/Linux

### Documentation
- Comprehensive README with architecture diagrams
- Quick start guide (START.md)
- Technical verification checklist (VERIFICATION.md)
- Executive summary (SUMMARY.md)
- Feature upgrade documentation (UPGRADE_SUMMARY.md)

## [0.1.0] - 2026-09-21

### Initial Release
- Basic dashboard with KPI cards
- Simple audit table view
- Live analyzer for project submission
- Database schema and seeding script
- Basic ML detection (Isolation Forest only)

---

**Legend:**
- 🗺️ Geospatial features
- 🇮🇳 Government/compliance features
- 📊 Data/reporting features
- 🌐 Localization features
- 🔍 AI/ML features
- 🛡️ Security features
- 👥 User management features
- 📸 Media features
- 🤖 LLM/AI features
- 📱 UI/UX features
- 🚀 Infrastructure features
