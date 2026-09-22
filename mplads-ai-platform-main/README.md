# 🛡️ MPLADS AI Platform
## AI-Powered Anomaly Detection System for MPLAD Scheme Implementation

[![SIH 2026](https://img.shields.io/badge/SIH-2026-blue)](https://sih.gov.in)
[![Problem Statement](https://img.shields.io/badge/PS-26102-green)](https://sih.gov.in)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-production--ready-brightgreen)](https://github.com)

> An end-to-end production-ready platform leveraging AI/ML to detect fraud, anomalies, and inefficiencies in India's MPLADS (Members of Parliament Local Area Development Scheme) implementation.

---

## 🎯 Problem Statement

**SIH 2026 - PS #26102:** Develop an AI-powered system to detect anomalies, fraud, and inefficiencies in MPLAD Scheme implementation for the Ministry of Statistics and Programme Implementation (MoSPI), Government of India.

---

## ✨ Key Features

### 🗺️ Interactive Geospatial Intelligence Hub
- **Live India Map** with 1,000+ projects visualization
- **Color-coded Risk Markers** (Critical/High/Medium/Low)
- **Animated Pulsing** for critical anomalies
- **GPS Deviation Vectors** showing sanctioned vs actual locations
- **Interactive Popups** with forensic details

### 📊 Executive Dashboard
- **12 Real-time KPI Cards** with government branding
- **MoSPI/GOI Standard** compliance badge 🇮🇳
- **Role-based Views** (Central Admin, District Officer, Auditor)
- **Live Clock** showing IST time
- **Priority Queue** for top 5% high-risk projects

### 🔍 5-Factor AI/ML Detection Engine
1. **Cost Anomaly** - Isolation Forest (30% weight)
2. **Timeline Delay** - Deadline deviation analysis (25% weight)
3. **Payment Mismatch** - Progress vs disbursement (20% weight)
4. **Geospatial Anomaly** - Haversine GPS verification (15% weight)
5. **Duplicate Detection** - Sentence-BERT similarity (10% weight)

### 🛠️ Additional Features
- ✅ **CSV Export** for CAG audit reports
- ✅ **Hash-chained Audit Logs** for tamper-evidence
- ✅ **Bilingual Support** (English/Hindi)
- ✅ **Ollama LLM Integration** with intelligent fallback
- ✅ **Human-in-the-Loop (HITL)** workflow
- ✅ **Evidence Photo Management** with SHA-256 verification

---

## 🏗️ Architecture

### Tech Stack

#### Frontend
- **Framework:** React 18 with Vite
- **Styling:** Tailwind CSS
- **Maps:** Leaflet.js 1.9.4
- **Charts:** Recharts
- **Icons:** Lucide React
- **HTTP Client:** Axios

#### Backend
- **Framework:** FastAPI (Python 3.13)
- **ORM:** SQLAlchemy (Async)
- **Database:** PostgreSQL / SQLite
- **ML/AI:** Scikit-learn, Sentence-BERT
- **Server:** Uvicorn

#### AI/ML Models
- **Isolation Forest** - Anomaly detection
- **Local Outlier Factor (LOF)** - Density-based detection
- **Sentence-BERT** - all-MiniLM-L6-v2 for text similarity
- **Haversine Formula** - Geospatial distance calculation

---

## 🚀 Quick Start

### Prerequisites
- **Node.js** 18+ and npm
- **Python** 3.10+
- **Git**
- **(Optional)** PostgreSQL
- **(Optional)** Ollama for LLM features

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/mplads-ai-platform.git
cd mplads-ai-platform

# Install dependencies
npm install

# Run the application
./start.sh
```

Or manually:

```bash
# Terminal 1 - Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm install
npm run dev
```

### Access the Application

- 🌐 **Frontend:** http://localhost:5173
- 🔧 **Backend API:** http://localhost:8000
- 📚 **API Docs:** http://localhost:8000/docs

---

## 📂 Project Structure

```
mplads-ai-platform/
├── backend/                    # Python FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI application entry
│   │   ├── database.py        # Database configuration
│   │   ├── models.py          # SQLAlchemy ORM models
│   │   ├── schemas.py         # Pydantic validation schemas
│   │   ├── ml_engine.py       # 5-factor ML detection engine
│   │   ├── llm_service.py     # Ollama LLM integration
│   │   └── routers/           # API route modules
│   ├── mplads.db              # SQLite database (seeded)
│   ├── requirements.txt       # Python dependencies
│   └── schema.sql             # Database schema
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   │   ├── Layout.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   └── Toast.jsx
│   │   ├── pages/             # Main application pages
│   │   │   ├── Dashboard.jsx  # Executive Dashboard
│   │   │   ├── GISMap.jsx     # Geospatial Intelligence Hub
│   │   │   ├── AuditTable.jsx # Interactive Audit Desk
│   │   │   └── LiveAnalyzer.jsx
│   │   ├── i18n/              # Internationalization
│   │   │   └── translations.js
│   │   ├── services/          # API client
│   │   │   └── api.js
│   │   ├── App.jsx            # Main app component
│   │   ├── main.jsx           # Entry point
│   │   └── index.css          # Global styles
│   ├── package.json
│   └── vite.config.js
│
├── scripts/
│   └── seed_db.py             # Database seeding script (1,050+ records)
│
├── docs/                       # Documentation
│   ├── START.md               # Quick start guide
│   ├── VERIFICATION.md        # Technical verification
│   └── SUMMARY.md             # Executive summary
│
├── logs/                       # Application logs (gitignored)
│
├── .env.example               # Environment template
├── .gitignore
├── package.json               # Root package (concurrently)
├── start.sh                   # Startup script
├── README.md                  # This file
└── UPGRADE_SUMMARY.md         # Feature upgrade documentation

```

---

## 🎬 Demo Walkthrough (8 Minutes)

### 1. Executive Dashboard (2 min)
- Show **MoSPI/GOI branding** at the top
- Highlight **12 real-time KPI cards**
- Demonstrate **role switching** (Admin/Officer/Auditor)
- Point out **live IST clock**

### 2. Geospatial Intelligence ⭐ (3 min)
- Navigate to **"Geospatial Intelligence"** in sidebar
- Zoom to show **India-wide map** with 1,000+ projects
- Click on a **red pulsing marker** (Critical anomaly)
- Explain:
  - Color-coded severity system
  - GPS deviation vectors (red dashed lines)
  - Distance calculations
- Click **"Open Forensic Desk"** button

### 3. Interactive Audit Desk (2 min)
- Show **flagged projects** table
- Demonstrate **"Export Forensic CSV"** button
- Search for **"MP-2024-8842"** (worked example)
- Display **5-factor risk breakdown**
- Show **hash-chained audit logs**

### 4. Live Analyzer (1 min)
- Submit a **test project proposal**
- Show **instant ML risk scoring**
- Mention **Sentence-BERT** and **Isolation Forest**

---

## 📊 Database Statistics

- **Total Projects:** 1,051
- **Flagged Projects:** ~195 (18.5%)
- **Critical Anomalies:** ~21 (2%)
- **High Risk:** ~53 (5%)
- **States Covered:** 7 major states
- **Districts:** 36 districts
- **Contractors:** 15 registered

### Worked Example: MP-2024-8842
- **Sanctioned Amount:** ₹25,00,000
- **Expenditure:** ₹22,50,000 (90%)
- **Physical Progress:** 35%
- **Payment Mismatch:** 55%
- **GPS Deviation:** 4.2 km
- **Status:** CRITICAL - Suspended

---

## 🔐 Security Features

1. **Tamper-Evident Audit Logs** - SHA-256 hash-chained records
2. **Role-Based Access Control (RBAC)** - Admin, Officer, Auditor roles
3. **Evidence Integrity** - SHA-256 photo verification
4. **Duplicate Detection** - Prevents evidence reuse across projects
5. **Secure API** - FastAPI with CORS middleware

---

## 🌐 API Endpoints

### Dashboard
- `GET /api/dashboard/kpis` - Aggregate statistics

### Projects
- `GET /api/projects/anomalies` - Flagged projects (paginated)
- `GET /api/projects/{id}` - Project details
- `POST /api/projects/analyze` - Real-time ML analysis
- `GET /api/projects/{id}/explain` - LLM audit report

### Database
- `POST /api/seed` - Reseed database with synthetic data

Full API documentation: http://localhost:8000/docs

---

## 🧪 Testing

### Backend Tests
```bash
cd backend
source venv/bin/activate
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Database Verification
```bash
cd backend
source venv/bin/activate
python ../scripts/seed_db.py
```

---

## 📈 Performance Metrics

- **ML Model Training:** ~2-3 seconds for 1,000+ records
- **API Response Time:** <200ms average
- **Frontend Build Time:** ~3 seconds
- **Page Load Time:** <1 second
- **Database Queries:** Optimized with async SQLAlchemy

---

## 🎓 Technical Highlights for Judges

### Innovation
- First-of-its-kind **geospatial fraud detection** for MPLADS
- **5-factor ensemble ML model** with weighted scoring
- **Real-time anomaly detection** with HITL workflow

### Production Readiness
- **Government branding** (MoSPI/GOI standards)
- **Bilingual interface** (English/Hindi)
- **CAG-compatible** CSV export format
- **Scalable architecture** (PostgreSQL-ready)

### Technical Sophistication
- **Async/Await** throughout stack
- **Hash-chained audit logs** (blockchain-inspired)
- **Sentence-BERT** NLP for duplicate detection
- **Leaflet.js** for interactive mapping

---

## 🤝 Contributing

This project was developed for **Smart India Hackathon 2026**. For contributions:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **Ministry of Statistics and Programme Implementation (MoSPI)**
- **Smart India Hackathon 2026**
- **Open Source Community** - React, FastAPI, Scikit-learn, Leaflet.js

---

## 📞 Support

For issues, questions, or feedback:
- Create an issue on GitHub
- Email: support@mplads-ai.gov.in (demo)
- Documentation: `/docs` folder

---

## 🎉 Project Status

✅ **Production Ready**  
✅ **Fully Documented**  
✅ **SIH 2026 Compliant**  
✅ **Deployment Ready**

**Built with ❤️ for Smart India Hackathon 2026**

---

**Last Updated:** September 22, 2026  
**Version:** 1.0.0  
**Status:** Active Development
