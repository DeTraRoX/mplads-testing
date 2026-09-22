import sys
import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# Ensure project root is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from app.database import get_db, Base, engine
from scripts.seed_db import seed_database_internal

router = APIRouter(prefix="/api/seed", tags=["Database Seed"])


@router.post("", status_code=status.HTTP_200_OK)
async def seed_database_endpoint(db: AsyncSession = Depends(get_db)):
    """Drops existing tables, creates new schema, and seeds 1,000+ synthetic MPLADS records."""
    try:
        count = await seed_database_internal(db)
        return {
            "status": "success",
            "message": f"Successfully initialized database tables and seeded {count} MPLADS projects with synthetic risk indicators.",
            "projects_seeded": count
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database seeding failed: {str(e)}"
        )
