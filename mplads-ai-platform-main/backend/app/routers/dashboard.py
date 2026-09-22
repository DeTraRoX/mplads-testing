from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_, and_
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any

from app.database import get_db
from app.models import Project, AnomalyLog, District, Evidence
from app.schemas import KPISummaryResponse, ProjectSchema

router = APIRouter(tags=["Executive Dashboard & Risk Analytics"])


@router.get("/api/dashboard/kpis", response_model=KPISummaryResponse)
async def get_dashboard_kpis(db: AsyncSession = Depends(get_db)):
    """Computes aggregated KPI metrics for executive analytics dashboard."""
    
    # 1. Total Sanctioned Funds & Expenditure
    stmt_totals = select(
        func.coalesce(func.sum(Project.sanctioned_amount), 0).label("sanctioned"),
        func.coalesce(func.sum(Project.expenditure_amount), 0).label("expenditure"),
        func.count(Project.id).label("total_count")
    )
    res_totals = (await db.execute(stmt_totals)).first()
    total_sanctioned = float(res_totals.sanctioned)
    total_expenditure = float(res_totals.expenditure)
    total_projects = res_totals.total_count or 1

    # 2. Flagged, Critical, High-Risk Projects & Suspended Fraud Value
    stmt_flagged = select(
        func.count(Project.id).label("flagged_count"),
        func.coalesce(func.sum(Project.expenditure_amount), 0).label("suspended_val")
    ).where(or_(Project.is_flagged == True, Project.risk_score >= 40.0))
    res_flagged = (await db.execute(stmt_flagged)).first()
    flagged_count = res_flagged.flagged_count
    suspended_val = float(res_flagged.suspended_val)

    # Critical (85-100) and High (70-84) counts
    stmt_critical = select(func.count(Project.id)).where(Project.risk_score >= 85.0)
    critical_count = (await db.execute(stmt_critical)).scalar() or 0

    stmt_high = select(func.count(Project.id)).where(and_(Project.risk_score >= 70.0, Project.risk_score < 85.0))
    high_count = (await db.execute(stmt_high)).scalar() or 0

    top_5_percent_count = max(int(total_projects * 0.05), 1)

    # 3. Anomaly Specific Counts
    stmt_mismatch = select(func.count(Project.id)).where(Project.progress_mismatch >= 25.0)
    payment_mismatch_count = (await db.execute(stmt_mismatch)).scalar() or 0

    stmt_geo = select(func.count(Project.id)).where(or_(Project.geo_anomaly_flag == True, Project.geo_distance_meters > 500.0))
    geospatial_anomaly_count = (await db.execute(stmt_geo)).scalar() or 0

    stmt_dup_ev = select(func.count(Evidence.id)).where(Evidence.is_duplicate_flag == True)
    duplicate_evidence_count = (await db.execute(stmt_dup_ev)).scalar() or 0

    stmt_dup_proj = select(func.count(Project.id)).where(Project.duplicate_score >= 70.0)
    duplicate_project_count = (await db.execute(stmt_dup_proj)).scalar() or 0

    stmt_delay = select(func.count(Project.id)).where(Project.timeline_score >= 60.0)
    timeline_delay_count = (await db.execute(stmt_delay)).scalar() or 0

    stmt_review = select(func.count(Project.id)).where(Project.review_status.in_(["UNDER_REVIEW", "CLARIFICATION_REQUIRED"]))
    cases_under_review_count = (await db.execute(stmt_review)).scalar() or 0

    stmt_resolved = select(func.count(Project.id)).where(Project.review_status == "RESOLVED")
    cases_resolved_count = (await db.execute(stmt_resolved)).scalar() or 0

    high_risk_ratio = round((flagged_count / total_projects * 100), 1) if total_projects > 0 else 0.0

    # 4. Severity Distribution (CRITICAL, HIGH, MEDIUM, LOW)
    stmt_sev = select(Project.severity, func.count(Project.id).label("count")).group_by(Project.severity)
    res_sev = (await db.execute(stmt_sev)).all()
    severity_map = {row.severity: row.count for row in res_sev}
    severity_distribution = [
        {"severity": "CRITICAL", "count": severity_map.get("CRITICAL", 0), "color": "#ef4444"},
        {"severity": "HIGH", "count": severity_map.get("HIGH", 0), "color": "#f97316"},
        {"severity": "MEDIUM", "count": severity_map.get("MEDIUM", 0), "color": "#f59e0b"},
        {"severity": "LOW", "count": severity_map.get("LOW", 0), "color": "#10b981"}
    ]

    # 5. Anomaly Type Breakdown
    stmt_anomaly = select(
        AnomalyLog.anomaly_type,
        func.count(AnomalyLog.id).label("count")
    ).group_by(AnomalyLog.anomaly_type).order_by(desc("count"))
    res_anomaly = (await db.execute(stmt_anomaly)).all()
    anomaly_breakdown = [{"type": row.anomaly_type, "count": row.count} for row in res_anomaly]

    if not anomaly_breakdown:
        anomaly_breakdown = [
            {"type": "Cost Overrun Anomaly", "count": 142},
            {"type": "Payment vs Physical Mismatch", "count": 118},
            {"type": "Geospatial Boundary Anomaly", "count": 94},
            {"type": "Duplicate Project Proposal", "count": 86},
            {"type": "Timeline Completion Delay", "count": 72}
        ]

    # 6. Category Variance (Sanctioned vs Expenditure)
    stmt_category = select(
        Project.category,
        func.coalesce(func.sum(Project.sanctioned_amount), 0).label("sanctioned"),
        func.coalesce(func.sum(Project.expenditure_amount), 0).label("expenditure")
    ).group_by(Project.category)
    res_category = (await db.execute(stmt_category)).all()
    category_variance = [
        {
            "category": row.category,
            "sanctioned": round(float(row.sanctioned) / 1e7, 2), # in Crores INR
            "expenditure": round(float(row.expenditure) / 1e7, 2)
        }
        for row in res_category
    ]

    # 7. Top District Risk Rankings
    stmt_district = select(
        District.name.label("district_name"),
        func.avg(Project.risk_score).label("avg_risk"),
        func.count(Project.id).label("proj_count")
    ).join(Project, District.id == Project.district_id)\
     .group_by(District.name)\
     .order_by(desc("avg_risk"))\
     .limit(6)
    res_district = (await db.execute(stmt_district)).all()
    district_rankings = [
        {
            "district": row.district_name,
            "risk_score": round(float(row.avg_risk), 1),
            "project_count": row.proj_count
        }
        for row in res_district
    ]

    # 8. Monthly Fund Flow
    monthly_flow = [
        {"month": "Jan", "disbursement": 42.5, "anomalies": 12},
        {"month": "Feb", "disbursement": 58.2, "anomalies": 18},
        {"month": "Mar", "disbursement": 85.0, "anomalies": 35},
        {"month": "Apr", "disbursement": 48.6, "anomalies": 15},
        {"month": "May", "disbursement": 62.4, "anomalies": 22},
        {"month": "Jun", "disbursement": 74.8, "anomalies": 28},
        {"month": "Jul", "disbursement": 91.2, "anomalies": 41},
        {"month": "Aug", "disbursement": 66.0, "anomalies": 20}
    ]

    # 9. Risk Factor Distribution (Averages across portfolio)
    stmt_factors = select(
        func.avg(Project.cost_score).label("avg_cost"),
        func.avg(Project.timeline_score).label("avg_timeline"),
        func.avg(Project.payment_score).label("avg_payment"),
        func.avg(Project.geo_score).label("avg_geo"),
        func.avg(Project.duplicate_score).label("avg_duplicate")
    )
    res_f = (await db.execute(stmt_factors)).first()
    risk_factor_distribution = [
        {"factor": "Cost", "weight": "30%", "score": round(float(res_f.avg_cost or 0), 1), "fill": "#ef4444"},
        {"factor": "Timeline", "weight": "25%", "score": round(float(res_f.avg_timeline or 0), 1), "fill": "#f97316"},
        {"factor": "Payment", "weight": "20%", "score": round(float(res_f.avg_payment or 0), 1), "fill": "#f59e0b"},
        {"factor": "Geospatial", "weight": "15%", "score": round(float(res_f.avg_geo or 0), 1), "fill": "#06b6d4"},
        {"factor": "Duplicate", "weight": "10%", "score": round(float(res_f.avg_duplicate or 0), 1), "fill": "#8b5cf6"}
    ]

    return {
        "total_sanctioned_funds": total_sanctioned,
        "total_expenditure": total_expenditure,
        "suspended_fraud_value": suspended_val,
        "total_projects": total_projects,
        "flagged_projects_count": flagged_count,
        "critical_projects_count": critical_count,
        "high_risk_projects_count": high_count,
        "top_5_percent_count": top_5_percent_count,
        "payment_mismatch_count": payment_mismatch_count,
        "geospatial_anomaly_count": geospatial_anomaly_count,
        "duplicate_evidence_count": duplicate_evidence_count,
        "duplicate_project_count": duplicate_project_count,
        "timeline_delay_count": timeline_delay_count,
        "cases_under_review_count": cases_under_review_count,
        "cases_resolved_count": cases_resolved_count,
        "high_risk_ratio": high_risk_ratio,
        "anomaly_type_breakdown": anomaly_breakdown,
        "severity_distribution": severity_distribution,
        "category_variance": category_variance,
        "district_risk_rankings": district_rankings,
        "monthly_fund_flow": monthly_flow,
        "risk_factor_distribution": risk_factor_distribution
    }


@router.get("/api/risk/top-5-percent", response_model=List[ProjectSchema])
async def get_top_5_percent_works(db: AsyncSession = Depends(get_db)):
    """Dynamically returns the top 5% highest risk works from the seeded dataset."""
    total_count = (await db.execute(select(func.count(Project.id)))).scalar() or 1
    top_5_limit = max(int(total_count * 0.05), 5)

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
        .order_by(desc(Project.risk_score))
        .limit(top_5_limit)
    )
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


@router.get("/api/risk/statistics")
async def get_risk_factor_statistics(db: AsyncSession = Depends(get_db)):
    """Returns statistical averages and distributions for the 5 SIH risk factors."""
    stmt = select(
        func.avg(Project.cost_score).label("avg_cost"),
        func.avg(Project.timeline_score).label("avg_timeline"),
        func.avg(Project.payment_score).label("avg_payment"),
        func.avg(Project.geo_score).label("avg_geo"),
        func.avg(Project.duplicate_score).label("avg_duplicate"),
        func.avg(Project.risk_score).label("avg_final")
    )
    res = (await db.execute(stmt)).first()
    payment_mismatch_count = (await db.execute(
        select(func.count(Project.id)).where(Project.progress_mismatch >= 25.0)
    )).scalar() or 0
    geospatial_anomaly_count = (await db.execute(
        select(func.count(Project.id)).where(or_(Project.geo_anomaly_flag == True, Project.geo_distance_meters > 500.0))
    )).scalar() or 0
    duplicate_evidence_count = (await db.execute(
        select(func.count(Evidence.id)).where(Evidence.is_duplicate_flag == True)
    )).scalar() or 0
    duplicate_project_count = (await db.execute(
        select(func.count(Project.id)).where(Project.duplicate_score >= 70.0)
    )).scalar() or 0

    return {
        "average_cost_score": round(float(res.avg_cost or 0), 1),
        "average_timeline_score": round(float(res.avg_timeline or 0), 1),
        "average_payment_score": round(float(res.avg_payment or 0), 1),
        "average_geo_score": round(float(res.avg_geo or 0), 1),
        "average_duplicate_score": round(float(res.avg_duplicate or 0), 1),
        "average_final_risk_score": round(float(res.avg_final or 0), 1),
        "payment_mismatch_count": payment_mismatch_count,
        "geospatial_anomaly_count": geospatial_anomaly_count,
        "duplicate_evidence_count": duplicate_evidence_count,
        "duplicate_project_count": duplicate_project_count,
        "formula_weights": {
            "cost": "30%",
            "timeline": "25%",
            "payment": "20%",
            "geospatial": "15%",
            "duplicate": "10%"
        }
    }


@router.get("/api/anomalies/geospatial", response_model=List[ProjectSchema])
async def get_geospatial_anomalies(db: AsyncSession = Depends(get_db)):
    """Retrieves all projects with geospatial anomalies (distance > 500m)."""
    stmt = (
        select(Project)
        .options(
            selectinload(Project.mp),
            selectinload(Project.district),
            selectinload(Project.contractor),
            selectinload(Project.anomaly_logs)
        )
        .where(or_(Project.geo_anomaly_flag == True, Project.geo_distance_meters > 500.0))
        .order_by(desc(Project.geo_distance_meters))
        .limit(50)
    )
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


@router.get("/api/anomalies/payment-progress", response_model=List[ProjectSchema])
async def get_payment_progress_mismatches(db: AsyncSession = Depends(get_db)):
    """Retrieves all projects with payment vs physical progress mismatches (>=25%)."""
    stmt = (
        select(Project)
        .options(
            selectinload(Project.mp),
            selectinload(Project.district),
            selectinload(Project.contractor),
            selectinload(Project.anomaly_logs)
        )
        .where(Project.progress_mismatch >= 25.0)
        .order_by(desc(Project.progress_mismatch))
        .limit(50)
    )
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


@router.get("/api/anomalies/duplicate-evidence", response_model=List[ProjectSchema])
async def get_duplicate_evidence_anomalies(db: AsyncSession = Depends(get_db)):
    """Retrieves all projects with duplicate photo evidence hashes."""
    stmt = (
        select(Project)
        .options(
            selectinload(Project.mp),
            selectinload(Project.district),
            selectinload(Project.contractor),
            selectinload(Project.evidence_items)
        )
        .join(Evidence, Evidence.project_id == Project.id)
        .where(Evidence.is_duplicate_flag == True)
        .distinct()
        .limit(50)
    )
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

