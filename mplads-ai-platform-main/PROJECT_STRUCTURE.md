# 📁 MPLADS AI Platform - Project Structure

## 🏗️ Industry-Grade Organization

```
mplads-ai-platform/
├── backend/                          # 🐍 Python FastAPI Backend
│   ├── app/                          # ── Application Code
│   │   ├── __init__.py
│   │   ├── main.py                   # 🎯 FastAPI entry point
│   │   ├── database.py               # 🔌 Database configuration
│   │   ├── models.py                 # 📊 SQLAlchemy ORM models
│   │   ├── schemas.py                # ✅ Pydantic validation
│   │   ├── ml_engine.py              # 🤖 5-Factor ML Detection Engine
│   │   ├── llm_service.py            # 💬 Ollama LLM Integration
│   │   ├── routes/                   # 🔗 API Routes
│   │   │   ├── seed.py               # 🚀 Database seeding
│   │   │   ├── dashboard.py          # 📈 Dashboard APIs
│   │   │   └── projects.py           # 📋 Project APIs
│   │   └── routers.json              # 🚦 Route definitions
│   ├── mplads.db                     # 💾 SQLite database (1,050+ records)
│   ├── requirements.txt              # 📦 Python dependencies
│   └── schema.sql                    # 🗄️ Database schema
│
├── frontend/                         # ⚛️ React Frontend
│   ├── src/                          # ── Source Code
│   │   ├── components/               # 🧩 Reusable UI Components
│   │   │   ├── Layout.jsx            # 📐 Page layout
│   │   │   ├── Sidebar.jsx           # 🧭 Navigation sidebar
│   │   │   ├── Toast.jsx             # 🔔 Notification system
│   │   │   └── StatCard.jsx          # 📊 KPI card component
│   │   │
│   │   ├── pages/                    # 📄 Main Pages
│   │   │   ├── Dashboard.jsx         # 🏠 Executive Dashboard
│   │   │   ├── GISMap.jsx            # 🗺️ Geospatial Intelligence Hub
│   │   │   ├── AuditTable.jsx        # 🔍 Interactive Audit Desk
│   │   │   └── LiveAnalyzer.jsx      # ⚡ Live Proposal Analyzer
│   │   │
│   │   ├── i18n/                     # 🌐 Internationalization
│   │   │   └── translations.js       # 🇺🇸/🇮🇳 EN/HI translations
│   │   │
│   │   ├── services/                 # 🌐 API Services
│   │   │   └── api.js                # 🔧 HTTP client (axios)
│   │   │
│   │   ├── App.jsx                   # 🎯 App router
│   │   ├── main.jsx                  # 🏁 Entry point
│   │   └── index.css                 # 🎨 Global styles
│   │
│   ├── package.json                  # 📦 Dependencies & scripts
│   ├── vite.config.js                # ⚡ Vite config
│   ├── tailwind.config.js            # 🎨 Tailwind CSS config
│   └── postcss.config.js             # 🎨 PostCSS config
│
├── scripts/                          # 🔧 Development Scripts
│   └── seed_db.py                    # 🚀 Database seeder (1,050+ records)
│
├── docs/                             # 📚 Documentation
│   ├── README.md                     # 📖 Main documentation
│   ├── START.md                      # ⚡ Quick start guide
│   ├── VERIFICATION.md               # ✅ Technical verification
│   ├── SUMMARY.md                      # 📊 Executive summary
│   ├── UPGRADE_SUMMARY.md            # 🆕 Feature upgrade notes
│   ├── ENVIRONMENT.md                # 🌍 Environment setup
│   └── DEPLOYMENT.md                 # 🚀 Production deployment
│
├── logs/                             # 📝 Application Logs (gitignored)
├── .github/                          # 🐙 GitHub Actions
│   └── workflows/
│       └── ci.yml                    # CI/CD pipeline
│
├── .env.example                      # 📋 Environment template
├── .gitignore                        # 🚫 Git ignores
├── .dockerignore                     # 🐳 Docker ignores
├── package.json                      # 📦 Root dependencies
├── start.sh                          # ⚙️ Startup script
├── CHANGELOG.md                      # 📝 Version history
├── CONTRIBUTING.md                   # 👥 Contribute guidelines
├── LICENSE                           # 📄 MIT License
├── README.md                         # 🎉 Project homepage
└── PROJECT_STRUCTURE.md              # 📁 This file
```

## 🎯 Key Technical Decisions

### Why This Structure?

1. **Clear Separation** - Backend and frontend are cleanly separated
2. **Industry Standards** - Follows Python and React best practices
3. **Modularity** - Components and pages are well-organized
4. **Documentation** - Comprehensive docs in `/docs` folder
5. **Scalability** - Ready for production deployment
6. **Maintainability** - Easy to understand and extend

### 🚀 Quick Commands

```bash
# Start development environment
./start.sh

# Build frontend for production
cd frontend && npm run build

# Run tests
cd backend && source venv/bin/activate && pytest

# Seed database
cd backend && source venv/bin/activate && python ../scripts/seed_db.py

# View logs
tail -f logs/backend.log
```

---

**Ready for production deployment!** 🚀
