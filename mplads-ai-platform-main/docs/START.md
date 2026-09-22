# 🚀 Quick Start Guide - MPLADS AI Platform

## ✅ Setup Complete!

All the upgrades from UPGRADE_SUMMARY.md have been verified and are working:

### What's Working:
1. ✅ **Interactive Geospatial Intelligence Hub** - `/map` page with Leaflet.js
2. ✅ **Enhanced Dashboard** - MoSPI/GOI branding with Indian flag 🇮🇳
3. ✅ **CSV Export Functionality** - Export forensic audit data
4. ✅ **Updated Navigation** - Geospatial Intelligence link in sidebar
5. ✅ **Bilingual Support** - English/Hindi translations
6. ✅ **Database** - SQLite with 1,000+ projects already seeded
7. ✅ **Frontend Build** - Successfully builds without errors

---

## 🎯 How to Run (macOS)

### Option 1: Run Both Frontend & Backend Together (Recommended)
```bash
npm run dev
```

### Option 2: Run Separately

#### Terminal 1 - Backend:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

---

## 🌐 Access the Application

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## 📊 Demo Flow (SIH Judges)

### 1. Dashboard (2 minutes)
- Start at http://localhost:5173
- Show MoSPI/GOI branding (top header)
- Point out 12 KPI cards with real-time data
- Show role switching (Central Admin / District Officer / Auditor)

### 2. Geospatial Intelligence (3 minutes)
- Click "Geospatial Intelligence" in sidebar
- Show interactive India map with 1,000+ projects
- Click on a **RED pulsing marker** (Critical anomaly)
- Point out:
  - Color-coded severity pins
  - GPS deviation vectors (red dashed lines)
  - Distance calculations
- Click "Open Forensic Desk" in popup

### 3. Audit Features (2 minutes)
- Go to "Interactive Audit Desk"
- Click "Export Forensic CSV" button
- Open one project to show 5-Factor SIH formula
- Show hash-chained audit logs

### 4. Live Analyzer (1 minute)
- Submit a new project proposal
- Show instant ML risk scoring
- Mention real Ollama LLM integration

---

## 🔧 Troubleshooting

### Backend Issues:
```bash
# Recreate virtual environment if needed
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Reseed Database:
```bash
# From project root
cd backend
source venv/bin/activate
python ../scripts/seed_db.py
```

### Frontend Issues:
```bash
cd frontend
rm -rf node_modules
npm install
npm run build
```

---

## 🎓 Key Technical Points for Judges

1. **5-Factor ML Engine:**
   - Isolation Forest (cost anomalies)
   - Sentence-BERT (duplicate detection)
   - Haversine formula (geospatial verification)
   - Payment-progress mismatch
   - Timeline delay detection

2. **Government Standards:**
   - MoSPI compliance branding
   - CAG audit trail compatibility
   - Role-based access control (RBAC)
   - Tamper-evident hash-chained logs

3. **Production Ready:**
   - PostgreSQL + SQLite support
   - CSV export for CAG reports
   - Multi-language support (EN/HI)
   - Interactive geospatial visualization

---

## 📝 Worked Example: Project MP-2024-8842

This is the showcase project in the database:
- **Sanctioned:** ₹25,00,000
- **Expenditure:** ₹22,50,000 (90%)
- **Physical Progress:** 35%
- **Mismatch:** 55%
- **GPS Deviation:** 4.2 km
- **Status:** CRITICAL - Suspended

Search for "MP-2024-8842" in the Audit Table to see this worked example.

---

## 🚀 Ready for Demo!

Everything is configured and working. Just run `npm run dev` and you're ready to impress the SIH judges!

**Good luck! 🎉**
