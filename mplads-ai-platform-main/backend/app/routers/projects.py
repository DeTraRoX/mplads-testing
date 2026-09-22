import hashlib
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, desc, func
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple
from datetime import datetime

from app.database import get_db
from app.models import (
    Project, AnomalyLog, MP, District, Contractor,
    Milestone, Evidence, AuditLog, Notification
)
from app.schemas import (
    ProjectSchema,
    MilestoneSchema,
    EvidenceSchema,
    EvidenceCreateRequest,
    AuditLogSchema,
    NotificationSchema,
    ReviewActionRequest,
    ClarificationRequest,
    ProjectAnalyzeRequest,
    ProjectAnalyzeResponse,
    ExecutiveExplanationResponse
)
from app.ml_engine import ml_engine, compute_sha256_hash
from app.llm_service import generate_executive_explanation
from app.routers.auth import check_role_permission

router = APIRouter(prefix="/api/projects", tags=["Project & Anomaly Audit"])


async def get_latest_audit_hash(db: AsyncSession, project_id: int) -> str:
    """Retrieves the previous audit hash for building a tamper-evident cryptographic hash chain."""
    stmt = select(AuditLog.record_hash).where(AuditLog.project_id == project_id).order_by(desc(AuditLog.id)).limit(1)
    res = await db.execute(stmt)
    latest = res.scalar()
    return latest if latest else "0" * 64


def generate_audit_record(
    project_id: int,
    action: str,
    old_value: Optional[str],
    new_value: Optional[str],
    remarks: Optional[str],
    username: str,
    previous_hash: str
) -> AuditLog:
    """Generates a cryptographic SHA-256 hash-chained AuditLog entity."""
    now = datetime.utcnow()
    content_payload = f"{previous_hash}|Project|{project_id}|{action}|{now.isoformat()}|{remarks or ''}"
    record_hash = hashlib.sha256(content_payload.encode("utf-8")).hexdigest()
    return AuditLog(
        project_id=project_id,
        user_id=None,
        username=username,
        action=action,
        entity_type="Project",
        entity_id=project_id,
        old_value=old_value,
        new_value=new_value,
        remarks=remarks,
        timestamp=now,
        previous_hash=previous_hash,
        record_hash=record_hash
    )


@router.get("/anomalies", response_model=List[ProjectSchema])
async def get_flagged_anomalies(
    search: Optional[str] = Query(None, description="Search by title, contractor, or location"),
    severity: Optional[str] = Query(None, description="Filter by severity: CRITICAL, HIGH, MEDIUM, LOW"),
    review_status: Optional[str] = Query(None, description="Filter by review status: AI_FLAGGED, UNDER_REVIEW, etc."),
    category: Optional[str] = Query(None, description="Filter by sector category"),
    top_5_percent: bool = Query(False, description="Filter only Top 5% Highest Risk works"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves filterable and paginated flagged projects with complete SIH risk data, evidence, and milestones."""
    stmt = (
        select(Project)
        .options(
            selectinload(Project.mp),
            selectinload(Project.district),
            selectinload(Project.contractor),
            selectinload(Project.anomaly_logs),
            selectinload(Project.milestones),
            selectinload(Project.evidence_items),
            selectinload(Project.audit_logs)
        )
    )

    if top_5_percent:
        # Calculate threshold for top 5%
        total_count = (await db.execute(select(func.count(Project.id)))).scalar() or 1
        top_5_limit = max(int(total_count * 0.05), 5)
        stmt = stmt.order_by(desc(Project.risk_score)).limit(top_5_limit)
        res = await db.execute(stmt)
        projects = res.scalars().unique().all()
        
        output = []
        for p in projects:
            item = ProjectSchema.model_validate(p)
            item.mp_name = p.mp.name if p.mp else "Unknown MP"
            item.district_name = p.district.name if p.district else "Unknown District"
            item.contractor_name = p.contractor.name if p.contractor else "Unknown Contractor"
            output.append(item)
        return output

    # Standard flagged filter
    stmt = stmt.where(or_(Project.is_flagged == True, Project.risk_score >= 40.0))

    if category:
        stmt = stmt.where(Project.category == category)

    if severity:
        stmt = stmt.where(Project.severity == severity.upper())

    if review_status:
        stmt = stmt.where(Project.review_status == review_status.upper())

    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Project.title.ilike(search_pattern),
                Project.location.ilike(search_pattern),
                Project.project_code.ilike(search_pattern)
            )
        )

    stmt = stmt.order_by(desc(Project.risk_score)).offset(offset).limit(limit)
    res = await db.execute(stmt)
    projects = res.scalars().unique().all()

    output = []
    for p in projects:
        item = ProjectSchema.model_validate(p)
        item.mp_name = p.mp.name if p.mp else "Unknown MP"
        item.district_name = p.district.name if p.district else "Unknown District"
        item.contractor_name = p.contractor.name if p.contractor else "Unknown Contractor"
        output.append(item)

    return output


@router.get("/{project_id}", response_model=ProjectSchema)
async def get_project_by_id(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves single project complete with milestones, evidence, and hash-chained audit trail."""
    stmt = (
        select(Project)
        .options(
            selectinload(Project.mp),
            selectinload(Project.district),
            selectinload(Project.contractor),
            selectinload(Project.anomaly_logs),
            selectinload(Project.milestones),
            selectinload(Project.evidence_items),
            selectinload(Project.audit_logs)
        )
        .where(Project.id == project_id)
    )
    project = (await db.execute(stmt)).scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    item = ProjectSchema.model_validate(project)
    item.mp_name = project.mp.name if project.mp else "Unknown MP"
    item.district_name = project.district.name if project.district else "Unknown District"
    item.contractor_name = project.contractor.name if project.contractor else "Unknown Contractor"
    return item


@router.get("/{project_id}/risk")
async def get_project_risk_breakdown(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Returns transparent SIH 5-factor risk formula breakdown for project."""
    stmt = select(Project).where(Project.id == project_id)
    p = (await db.execute(stmt)).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "project_id": p.id,
        "project_code": p.project_code,
        "title": p.title,
        "cost_score": float(p.cost_score or 0.0),
        "timeline_score": float(p.timeline_score or 0.0),
        "payment_score": float(p.payment_score or 0.0),
        "geo_score": float(p.geo_score or 0.0),
        "duplicate_score": float(p.duplicate_score or 0.0),
        "matched_proposal_title": p.matched_proposal_title,
        "duplicate_similarity_ratio": float(p.duplicate_similarity_ratio or 0.0),
        "final_risk_score": float(p.risk_score or 0.0),
        "severity": p.severity,
        "payment_progress": float(p.payment_progress or 0.0),
        "physical_progress": float(p.physical_progress or 0.0),
        "progress_mismatch": float(p.progress_mismatch or 0.0),
        "geo_distance_meters": float(p.geo_distance_meters or 0.0),
        "geo_anomaly_flag": bool(p.geo_anomaly_flag)
    }


@router.get("/{project_id}/evidence", response_model=List[EvidenceSchema])
async def get_project_evidence(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Returns evidence gallery and SHA-256 hashes for project."""
    stmt = select(Evidence).where(Evidence.project_id == project_id).order_by(desc(Evidence.uploaded_at))
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/{project_id}/milestones", response_model=List[MilestoneSchema])
async def get_project_milestones(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Returns milestone tracking timeline for project."""
    stmt = select(Milestone).where(Milestone.project_id == project_id).order_by(Milestone.planned_start_date)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/{project_id}/audit", response_model=List[AuditLogSchema])
async def get_project_audit_trail(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Returns tamper-evident cryptographic hash chain audit records."""
    stmt = select(AuditLog).where(AuditLog.project_id == project_id).order_by(desc(AuditLog.timestamp))
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/{project_id}/notifications", response_model=List[NotificationSchema])
async def get_project_notifications(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves all in-app notifications generated for a specific project."""
    stmt = select(Notification).where(Notification.project_id == project_id).order_by(desc(Notification.created_at))
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/{project_id}/view")
async def record_project_view(
    project_id: int,
    username: Optional[str] = Query("Inspector"),
    db: AsyncSession = Depends(get_db)
):
    """Logs a tamper-evident PROJECT_VIEWED audit trail record."""
    prev_hash = await get_latest_audit_hash(db, project_id)
    audit_log = generate_audit_record(
        project_id=project_id,
        action="PROJECT_VIEWED",
        old_value=None,
        new_value="VIEWED",
        remarks=f"Project record inspected by {username}",
        username=username or "Inspector",
        previous_hash=prev_hash
    )
    db.add(audit_log)
    await db.commit()
    return {"status": "success", "action": "PROJECT_VIEWED", "record_hash": audit_log.record_hash}


@router.post("/{project_id}/review", response_model=ProjectSchema)
async def review_project_case(
    project_id: int,
    payload: ReviewActionRequest,
    current_user = Depends(check_role_permission(["ADMIN", "DISTRICT_OFFICER"])),
    db: AsyncSession = Depends(get_db)
):
    """Moves case status to UNDER_REVIEW and logs tamper-evident audit record."""
    stmt = select(Project).where(Project.id == project_id)
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    old_status = project.review_status
    project.review_status = "UNDER_REVIEW"
    project.review_remarks = payload.remarks

    # Audit Trail
    prev_hash = await get_latest_audit_hash(db, project_id)
    audit_log = generate_audit_record(
        project_id=project_id,
        action="STATUS_CHANGED_TO_UNDER_REVIEW",
        old_value=old_status,
        new_value="UNDER_REVIEW",
        remarks=payload.remarks,
        username=payload.username or "Officer",
        previous_hash=prev_hash
    )
    db.add(audit_log)

    await db.commit()
    return await get_project_by_id(project_id, db)


@router.post("/{project_id}/clarification", response_model=ProjectSchema)
async def request_project_clarification(
    project_id: int,
    payload: ClarificationRequest,
    current_user = Depends(check_role_permission(["ADMIN", "DISTRICT_OFFICER"])),
    db: AsyncSession = Depends(get_db)
):
    """Issues formal clarification request, flags case as CLARIFICATION_REQUIRED, and triggers notification."""
    stmt = select(Project).where(Project.id == project_id)
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    old_status = project.review_status
    project.review_status = "CLARIFICATION_REQUIRED"
    project.review_remarks = payload.remarks

    # Audit Trail
    prev_hash = await get_latest_audit_hash(db, project_id)
    audit_log = generate_audit_record(
        project_id=project_id,
        action="CLARIFICATION_REQUESTED",
        old_value=old_status,
        new_value="CLARIFICATION_REQUIRED",
        remarks=f"To: {payload.requested_to} | Remarks: {payload.remarks}",
        username=payload.username or getattr(current_user, "full_name", None) or "Auditor",
        previous_hash=prev_hash
    )
    db.add(audit_log)

    # In-App Notification
    notif = Notification(
        project_id=project.id,
        title="Clarification Requested",
        message=f"Clarification issued for '{project.project_code}' ({project.title}): {payload.remarks}",
        severity="HIGH"
    )
    db.add(notif)

    await db.commit()
    return await get_project_by_id(project_id, db)


@router.post("/{project_id}/verify", response_model=ProjectSchema)
async def verify_project_anomaly(
    project_id: int,
    payload: ReviewActionRequest,
    current_user = Depends(check_role_permission(["ADMIN", "DISTRICT_OFFICER"])),
    db: AsyncSession = Depends(get_db)
):
    """Verifies that the flagged anomaly is substantiated by field evidence and logs audit record."""
    stmt = select(Project).where(Project.id == project_id)
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    old_status = project.review_status
    project.review_status = "VERIFIED"
    project.review_remarks = payload.remarks

    prev_hash = await get_latest_audit_hash(db, project_id)
    audit_log = generate_audit_record(
        project_id=project_id,
        action="PROJECT_VERIFIED",
        old_value=old_status,
        new_value="VERIFIED",
        remarks=payload.remarks,
        username=payload.username or getattr(current_user, "full_name", None) or "Officer",
        previous_hash=prev_hash
    )
    db.add(audit_log)

    await db.commit()
    return await get_project_by_id(project_id, db)


@router.post("/{project_id}/dismiss", response_model=ProjectSchema)
async def dismiss_project_anomaly(
    project_id: int,
    payload: ReviewActionRequest,
    current_user = Depends(check_role_permission(["ADMIN", "DISTRICT_OFFICER"])),
    db: AsyncSession = Depends(get_db)
):
    """Dismisses false positive anomaly with justification remarks and logs audit record."""
    stmt = select(Project).where(Project.id == project_id)
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    old_status = project.review_status
    project.review_status = "DISMISSED"
    project.is_flagged = False
    project.review_remarks = payload.remarks

    prev_hash = await get_latest_audit_hash(db, project_id)
    audit_log = generate_audit_record(
        project_id=project_id,
        action="PROJECT_DISMISSED",
        old_value=old_status,
        new_value="DISMISSED",
        remarks=payload.remarks,
        username=payload.username or getattr(current_user, "full_name", None) or "Auditor",
        previous_hash=prev_hash
    )
    db.add(audit_log)

    await db.commit()
    return await get_project_by_id(project_id, db)


@router.post("/{project_id}/resolve", response_model=ProjectSchema)
async def resolve_project_case(
    project_id: int,
    payload: ReviewActionRequest,
    current_user = Depends(check_role_permission(["ADMIN", "DISTRICT_OFFICER"])),
    db: AsyncSession = Depends(get_db)
):
    """Marks case as RESOLVED after corrective measures or contractor explanation."""
    stmt = select(Project).where(Project.id == project_id)
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    old_status = project.review_status
    project.review_status = "RESOLVED"
    project.is_flagged = False
    project.review_remarks = payload.remarks

    prev_hash = await get_latest_audit_hash(db, project_id)
    audit_log = generate_audit_record(
        project_id=project_id,
        action="PROJECT_RESOLVED",
        old_value=old_status,
        new_value="RESOLVED",
        remarks=payload.remarks,
        username=payload.username or getattr(current_user, "full_name", None) or "Admin",
        previous_hash=prev_hash
    )
    db.add(audit_log)

    notif = Notification(
        project_id=project.id,
        title="Case Resolved",
        message=f"Project '{project.project_code}' case has been marked as RESOLVED by {payload.username}.",
        severity="LOW"
    )
    db.add(notif)

    await db.commit()
    return await get_project_by_id(project_id, db)


@router.post("/{project_id}/evidence", response_model=EvidenceSchema)
async def upload_project_evidence(
    project_id: int,
    payload: EvidenceCreateRequest,
    current_user = Depends(check_role_permission(["ADMIN", "DISTRICT_OFFICER"])),
    db: AsyncSession = Depends(get_db)
):
    """Attaches site photo evidence with SHA-256 hash and verifies duplicate image reuse."""
    stmt = select(Project).where(Project.id == project_id)
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    img_bytes = payload.image_path.encode("utf-8")
    img_hash = compute_sha256_hash(img_bytes)

    # Check for duplicate image hash across other projects
    stmt_dup = select(Evidence).where(Evidence.image_hash == img_hash, Evidence.project_id != project_id)
    dup_exists = (await db.execute(stmt_dup)).scalars().first()
    is_duplicate = dup_exists is not None

    evidence = Evidence(
        project_id=project_id,
        image_path=payload.image_path,
        image_hash=img_hash,
        latitude=payload.latitude or project.actual_latitude,
        longitude=payload.longitude or project.actual_longitude,
        uploaded_by=payload.uploaded_by or "Field Inspector",
        description=payload.description,
        is_duplicate_flag=is_duplicate
    )
    db.add(evidence)

    # Audit log
    prev_hash = await get_latest_audit_hash(db, project_id)
    audit_log = generate_audit_record(
        project_id=project_id,
        action="EVIDENCE_ADDED",
        old_value=None,
        new_value=f"Hash: {img_hash[:16]}... | Duplicate: {is_duplicate}",
        remarks=payload.description or "Photo evidence attached",
        username=payload.uploaded_by or "Inspector",
        previous_hash=prev_hash
    )
    db.add(audit_log)

    if is_duplicate:
        notif = Notification(
            project_id=project.id,
            title="Duplicate Evidence Detected",
            message=f"Photo uploaded to '{project.project_code}' matches existing image hash in Project #{dup_exists.project_id}.",
            severity="CRITICAL"
        )
        db.add(notif)

    await db.commit()
    await db.refresh(evidence)
    return evidence


@router.post("/analyze", response_model=ProjectAnalyzeResponse)
async def analyze_new_project_proposal(
    payload: ProjectAnalyzeRequest,
    db: AsyncSession = Depends(get_db)
):
    """Evaluates a new project proposal in real time against the SIH 5-Factor Risk Formula."""
    # Check contractor blacklist status in DB if exists
    stmt_contractor = select(Contractor).where(Contractor.gstin == payload.contractor_gstin)
    res_c = (await db.execute(stmt_contractor)).scalar_one_or_none()
    is_blacklisted = res_c.blacklisted_status if res_c else False

    # Fit the ML engine only when the first live analysis is requested.
    # This keeps Sentence-BERT out of FastAPI startup memory while still using
    # the full historical-project semantic duplicate detector.
    if not ml_engine.is_fitted:
        historical_stmt = select(Project).order_by(Project.id)
        historical_result = await db.execute(historical_stmt)
        historical_projects = historical_result.scalars().all()
        historical_records = [
            {
                "title": p.title,
                "description": p.description or "",
                "category": p.category,
                "sanctioned_amount": float(p.sanctioned_amount or 0),
                "expenditure_amount": float(p.expenditure_amount or 0),
                "start_date": p.start_date,
                "target_completion_date": p.target_completion_date,
            }
            for p in historical_projects
        ]
        ml_engine.fit(historical_records)

    analysis = ml_engine.analyze_project(
        title=payload.title,
        description=payload.location,
        category=payload.category,
        sanctioned_amount=payload.sanctioned_amount,
        expenditure_amount=payload.expenditure_amount,
        start_date=str(payload.start_date),
        target_completion_date=str(payload.target_completion_date),
        contractor_name=payload.contractor_name,
        contractor_gstin=payload.contractor_gstin,
        district_name=payload.district_name,
        physical_progress=payload.physical_progress,
        sanctioned_lat=payload.sanctioned_latitude,
        sanctioned_lon=payload.sanctioned_longitude,
        actual_lat=payload.actual_latitude,
        actual_lon=payload.actual_longitude,
        is_contractor_blacklisted=is_blacklisted,
        delay_months=payload.delay_months
    )

    return analysis


@router.get("/{project_id}/explain", response_model=ExecutiveExplanationResponse)
async def explain_project_anomaly(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Triggers local Ollama LLM / domain-specific fallback generator for 2-sentence executive audit report."""
    stmt = (
        select(Project)
        .options(
            selectinload(Project.district),
            selectinload(Project.contractor),
            selectinload(Project.anomaly_logs)
        )
        .where(Project.id == project_id)
    )
    project = (await db.execute(stmt)).scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    anomaly_types = [a.anomaly_type for a in project.anomaly_logs]

    # Check cached explanation in anomaly logs
    for log in project.anomaly_logs:
        if log.llm_explanation:
            return ExecutiveExplanationResponse(
                project_id=project.id,
                project_title=project.title,
                risk_score=float(project.risk_score),
                executive_summary=log.llm_explanation,
                generated_at=datetime.utcnow()
            )

    # Call LLM service
    project_dict = {
        "title": project.title,
        "category": project.category,
        "sanctioned_amount": float(project.sanctioned_amount),
        "expenditure_amount": float(project.expenditure_amount),
        "risk_score": float(project.risk_score),
        "contractor_name": project.contractor.name if project.contractor else "N/A",
        "district_name": project.district.name if project.district else "N/A",
        "anomalies": anomaly_types
    }

    explanation = await generate_executive_explanation(project_dict)

    if project.anomaly_logs:
        project.anomaly_logs[0].llm_explanation = explanation
        await db.commit()

    return ExecutiveExplanationResponse(
        project_id=project.id,
        project_title=project.title,
        risk_score=float(project.risk_score),
        executive_summary=explanation,
        generated_at=datetime.utcnow()
    )


def _serialize_project(p: Project) -> ProjectSchema:
    item = ProjectSchema.model_validate(p)
    item.mp_name = p.mp.name if p.mp else "Unknown MP"
    item.district_name = p.district.name if p.district else "Unknown District"
    item.contractor_name = p.contractor.name if p.contractor else "Unknown Contractor"
    return item


@router.get("/code/{project_code}", response_model=ProjectSchema)
async def get_project_by_code(
    project_code: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves a project by unique code (e.g. MP-2024-8842)."""
    stmt = (
        select(Project)
        .options(
            selectinload(Project.mp),
            selectinload(Project.district),
            selectinload(Project.contractor),
            selectinload(Project.anomaly_logs),
            selectinload(Project.milestones),
            selectinload(Project.evidence_items),
            selectinload(Project.audit_logs)
        )
        .where(Project.project_code == project_code)
    )
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return _serialize_project(project)


@router.get("", response_model=List[ProjectSchema])
async def list_all_projects(
    search: Optional[str] = Query(None, description="Search by title, location, or project code"),
    severity: Optional[str] = Query(None, description="Filter by severity: CRITICAL, HIGH, MEDIUM, LOW"),
    review_status: Optional[str] = Query(None, description="Filter by review status"),
    category: Optional[str] = Query(None, description="Filter by sector category"),
    top_5_percent: bool = Query(False, description="Return only the dynamic top 5% highest-risk works"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves projects with severity, review status, category, search, and top-5% filters."""
    stmt = (
        select(Project)
        .options(
            selectinload(Project.mp),
            selectinload(Project.district),
            selectinload(Project.contractor),
            selectinload(Project.anomaly_logs),
            selectinload(Project.milestones),
            selectinload(Project.evidence_items),
            selectinload(Project.audit_logs)
        )
    )

    if top_5_percent:
        total_count = (await db.execute(select(func.count(Project.id)))).scalar() or 1
        top_5_limit = max(int(total_count * 0.05), 5)
        stmt = stmt.order_by(desc(Project.risk_score)).limit(top_5_limit)
        res = await db.execute(stmt)
        return [_serialize_project(p) for p in res.scalars().unique().all()]

    if category:
        stmt = stmt.where(Project.category == category)
    if severity:
        stmt = stmt.where(Project.severity == severity.upper())
    if review_status:
        stmt = stmt.where(Project.review_status == review_status.upper())
    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Project.title.ilike(search_pattern),
                Project.location.ilike(search_pattern),
                Project.project_code.ilike(search_pattern)
            )
        )

    stmt = stmt.order_by(desc(Project.risk_score)).offset(offset).limit(limit)
    res = await db.execute(stmt)
    return [_serialize_project(p) for p in res.scalars().unique().all()]

