from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update
from typing import List, Optional

from app.database import get_db
from app.models import Notification
from app.schemas import NotificationSchema

router = APIRouter(prefix="/api/notifications", tags=["In-App Notifications"])

@router.get("", response_model=List[NotificationSchema])
async def list_notifications(
    unread_only: bool = Query(False, description="Filter only unread notifications"),
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves in-app system notifications for risk anomalies, mismatches, and case resolutions."""
    stmt = select(Notification)
    if unread_only:
        stmt = stmt.where(Notification.is_read == False)
    stmt = stmt.order_by(desc(Notification.created_at)).limit(limit)
    res = await db.execute(stmt)
    notifications = res.scalars().all()
    return notifications

@router.put("/{notification_id}/read", response_model=NotificationSchema)
async def mark_notification_as_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Marks an individual notification as read."""
    stmt = select(Notification).where(Notification.id == notification_id)
    notif = (await db.execute(stmt)).scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    await db.commit()
    await db.refresh(notif)
    return notif

@router.post("/mark-all-read")
async def mark_all_notifications_as_read(db: AsyncSession = Depends(get_db)):
    """Marks all pending notifications as read."""
    await db.execute(update(Notification).values(is_read=True))
    await db.commit()
    return {"status": "success", "message": "All notifications marked as read"}
