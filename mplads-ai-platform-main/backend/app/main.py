import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Add backend and root directories to sys.path to resolve imports cleanly
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root_dir = os.path.dirname(backend_dir)
for d in [backend_dir, root_dir]:
    if d not in sys.path:
        sys.path.insert(0, d)
#importing libs


from app.database import init_db, AsyncSessionLocal
from app.routers.seed import router as seed_router
from app.routers.dashboard import router as dashboard_router
from app.routers.projects import router as projects_router
from app.routers.notifications import router as notifications_router
from app.routers.auth import router as auth_router
from app.ml_engine import ml_engine
from scripts.seed_db import seed_database_internal

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for database initialization and ML model warm-up."""
    # Ensure tables exist without breaking server startup if network is transiently unreachable
    try:
        await init_db()
    except Exception as err:
        print(f"[MPLADS Startup] Database connection notice during startup: {err}")

    # Pre-seed sample database if completely empty
    async with AsyncSessionLocal() as session:
        try:
            seeded_count = await seed_database_internal(session, force_if_empty=True)
            if seeded_count > 0:
                print(f"[MPLADS Startup] Pre-populated database with {seeded_count} project records.")
        except Exception as err:
            print(f"[MPLADS Startup] Seeding notice: {err}")

    yield

app = FastAPI(
    title="MPLAD Scheme AI-Powered Anomaly & Fraud Detection API",
    description="Backend Web API providing ML-driven financial audit, duplicate detection, and LLM executive summaries for Indian MPLAD scheme implementation.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration allowing React client (http://localhost:5173)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "https://mplads-testing-1.onrender.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(auth_router)
app.include_router(seed_router)
app.include_router(dashboard_router)
app.include_router(projects_router)
app.include_router(notifications_router)

@app.get("/")
async def root_health_check():
    return {
        "status": "online",
        "service": "MPLADS Scheme AI Detection Platform API",
        "documentation": "/docs",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), workers=1)
