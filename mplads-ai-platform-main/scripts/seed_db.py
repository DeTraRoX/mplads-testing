import sys
import os

# ── Force SQLite for standalone seed execution ──────────────────────────────
# Must be set BEFORE any app imports that read DATABASE_URL at module load time.
# This avoids Supabase/PgBouncer DDL timeout when running drop_all/create_all.
_BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
_SQLITE_PATH = os.path.join(_BACKEND_DIR, "mplads.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_SQLITE_PATH}"
# ─────────────────────────────────────────────────────────────────────────────

import random
import asyncio
import hashlib
from datetime import date, timedelta, datetime
from sqlalchemy import select, func, text

# Ensure python path can find backend packages
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(_BACKEND_DIR)

from app.database import AsyncSessionLocal, init_db, engine, Base
from app.models import (
    User, MP, District, Contractor, Project,
    Milestone, Evidence, FundDisbursement, AnomalyLog,
    AuditLog, Notification
)
from app.ml_engine import ml_engine, calculate_haversine_distance, compute_sha256_hash

STATES_AND_DISTRICTS = {
    "Uttar Pradesh": ["Varanasi", "Gorakhpur", "Lucknow", "Prayagraj", "Kanpur Nagar", "Agra"],
    "Maharashtra": ["Mumbai Suburban", "Pune", "Nagpur", "Nashik", "Thane", "Chhatrapati Sambhajinagar"],
    "Bihar": ["Patna", "Gaya", "Muzaffarpur", "Bhagalpur", "Darbhanga"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem"],
    "West Bengal": ["Kolkata", "Howrah", "North 24 Parganas", "Murshidabad", "Darjeeling"],
    "Karnataka": ["Bengaluru Urban", "Mysuru", "Belagavi", "Dharwad", "Dakshina Kannada"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Bikaner"]
}

DISTRICT_COORDINATES = {
    "Varanasi": (25.3176, 82.9739),
    "Gorakhpur": (26.7606, 83.3732),
    "Lucknow": (26.8467, 80.9462),
    "Prayagraj": (25.4358, 81.8463),
    "Kanpur Nagar": (26.4499, 80.3319),
    "Agra": (27.1767, 78.0081),
    "Mumbai Suburban": (19.0760, 72.8777),
    "Pune": (18.5204, 73.8567),
    "Nagpur": (21.1458, 79.0882),
    "Nashik": (19.9975, 73.7898),
    "Thane": (19.2183, 72.9781),
    "Chhatrapati Sambhajinagar": (19.8762, 75.3433),
    "Patna": (25.5941, 85.1376),
    "Gaya": (24.7914, 85.0002),
    "Muzaffarpur": (26.1209, 85.3647),
    "Bhagalpur": (25.2425, 86.9842),
    "Darbhanga": (26.1542, 85.8918),
    "Chennai": (13.0827, 80.2707),
    "Coimbatore": (11.0168, 76.9558),
    "Madurai": (9.9252, 78.1198),
    "Tiruchirappalli": (10.7905, 78.7047),
    "Salem": (11.6643, 78.1460),
    "Kolkata": (22.5726, 88.3639),
    "Howrah": (22.5958, 88.2636),
    "North 24 Parganas": (22.7230, 88.4800),
    "Murshidabad": (24.1759, 88.2802),
    "Darjeeling": (27.0410, 88.2663),
    "Bengaluru Urban": (12.9716, 77.5946),
    "Mysuru": (12.2958, 76.6394),
    "Belagavi": (15.8497, 74.4977),
    "Dharwad": (15.4589, 75.0078),
    "Dakshina Kannada": (12.8700, 74.8800),
    "Jaipur": (26.9124, 75.7873),
    "Jodhpur": (26.2389, 73.0243),
    "Udaipur": (24.5854, 73.7125),
    "Kota": (25.2138, 75.8648),
    "Bikaner": (28.0229, 73.3119)
}

POLITICAL_PARTIES = ["BJP", "INC", "TMC", "DMK", "AAP", "SP", "JD(U)", "Independent"]

CATEGORIES = [
    "Roads & Bridges",
    "Drinking Water & Sanitation",
    "Education & School Infrastructure",
    "Public Health & Hospitals",
    "Community Halls & Libraries",
    "Solar Lighting & Electricity",
    "Sports & Youth Infrastructure"
]

CONTRACTOR_NAMES = [
    "Apex Infrastructure Pvt Ltd", "Shiv Shakti Builders", "Vanguard Civil Works",
    "Bharat Development Infra", "Surya Construction Corp", "Shree Ram Engineering",
    "Himalaya Earthmovers", "Greenland Eco Infrastructure", "National Highway Engineers",
    "Mahadev Enterprises", "Imperial Projects India", "Metro City Constructions",
    "Zenith Structural Solutions", "Pacific Civil Infra", "Trident Developers"
]

PROJECT_TITLE_TEMPLATES = [
    "Construction of CC Road and Covered Drain in {location}",
    "Installation of Solar Powered Deep Borewell and Hand Pump at {location}",
    "Construction of Additional Classroom Block at Government High School, {location}",
    "Setup of Public Library and Multi-Purpose Community Hall in {location}",
    "Installation of High-Mast LED Street Lighting System in {location}",
    "Upgradation and Renovation of Primary Health Sub-Centre at {location}",
    "Paving of Interlocking Block Pathways and Boundary Wall in {location}",
    "Supply of Computer Equipment and Smart Board to Government College in {location}"
]

SAMPLE_IMAGE_PLACEHOLDERS = [
    "https://images.unsplash.com/photo-1541888946425-d0fbb186156f?w=600&auto=format&fit=crop", # Construction
    "https://images.unsplash.com/photo-1590381105924-c72589b9ef3f?w=600&auto=format&fit=crop", # Road work
    "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=600&auto=format&fit=crop", # Concrete structure
    "https://images.unsplash.com/photo-1581094794329-c8112a89af12?w=600&auto=format&fit=crop", # Field inspection
    "https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=600&auto=format&fit=crop"  # Building site
]

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

async def seed_database_internal(db_session, force_if_empty=False) -> int:
    """Populates 1,000+ realistic records with complete SIH formula anomalies, worked case MP-2024-8842, evidence photos, and audit chains."""
    
    # Check if data already exists unless forced
    stmt_check = select(func.count(Project.id))
    existing_count = (await db_session.execute(stmt_check)).scalar()
    
    if existing_count > 0 and force_if_empty:
        return 0

    # 1. Drop and recreate all tables to ensure schema reflects new columns
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # 2. Seed Prototype Users for RBAC
    users_data = [
        User(username="admin", password_hash=hash_password("admin123"), full_name="Shri Alok Verma (Joint Secretary)", role="ADMIN", district_name=None),
        User(username="district_officer", password_hash=hash_password("officer123"), full_name="Dr. S. K. Dwivedi (District Magistrate)", role="DISTRICT_OFFICER", district_name="Varanasi"),
        User(username="auditor", password_hash=hash_password("auditor123"), full_name="Pooja Sen (CAG Lead Auditor)", role="AUDITOR", district_name=None)
    ]
    for u in users_data:
        db_session.add(u)
    await db_session.flush()

    # 3. Create MPs
    mps = []
    for state, districts in STATES_AND_DISTRICTS.items():
        for d in districts:
            mp = MP(
                name=f"Shri {random.choice(['Rajesh', 'Suresh', 'Amit', 'Sunil', 'Vijay', 'Ramesh', 'Priya', 'Anita'])} {random.choice(['Sharma', 'Verma', 'Singh', 'Patel', 'Yadav', 'Rao', 'Kumar'])}",
                constituency=f"{d} Parliamentary Constituency",
                state=state,
                party=random.choice(POLITICAL_PARTIES),
                allocated_budget=50000000.00,
                utilized_budget=0.00
            )
            db_session.add(mp)
            mps.append(mp)
    await db_session.flush()

    # 4. Create Districts
    districts = []
    dist_map = {}
    for state, dist_names in STATES_AND_DISTRICTS.items():
        for d_name in dist_names:
            dist = District(
                name=d_name,
                state=state,
                nodal_agency=f"District Rural Development Agency (DRDA), {d_name}",
                risk_score=round(random.uniform(10.0, 45.0), 1)
            )
            db_session.add(dist)
            districts.append(dist)
            dist_map[d_name] = dist
    await db_session.flush()

    # 5. Create Contractors
    contractors = []
    for idx, c_name in enumerate(CONTRACTOR_NAMES):
        is_blacklisted = (idx == 2 or idx == 7) # Contractors 2 & 7 blacklisted
        contractor = Contractor(
            name=c_name,
            gstin=f"07{random.randint(1000, 9999)}A1Z{idx}P{idx}",
            rating=round(random.uniform(2.1, 4.9) if not is_blacklisted else random.uniform(1.0, 2.0), 2),
            blacklisted_status=is_blacklisted,
            registered_date=date(2018, 1, 1) + timedelta(days=idx*120)
        )
        db_session.add(contractor)
        contractors.append(contractor)
    await db_session.flush()

    # Find Varanasi district and Apex contractor for the Worked Case
    varanasi_dist = dist_map.get("Varanasi", districts[0])
    apex_contractor = contractors[0]
    varanasi_mp = [m for m in mps if "Varanasi" in m.constituency][0] if any("Varanasi" in m.constituency for m in mps) else mps[0]

    # Bootstrap Isolation Forest / LOF / text models so ensemble scoring is active during seed
    bootstrap_history = []
    for k in range(90):
        sanctioned_b = float(random.randint(5, 60) * 100000)
        if k < 12:
            expenditure_b = round(sanctioned_b * random.uniform(1.4, 1.8), 2)
        else:
            expenditure_b = round(sanctioned_b * random.uniform(0.72, 1.05), 2)
        bootstrap_history.append({
            "title": f"Baseline civic infrastructure work {k} in Ward {k % 40 + 1}",
            "description": "Standard MPLADS civic works used to calibrate cost outlier detectors.",
            "category": random.choice(CATEGORIES),
            "sanctioned_amount": sanctioned_b,
            "expenditure_amount": expenditure_b,
            "start_date": "2024-01-01",
            "target_completion_date": "2024-07-01"
        })
    ml_engine.fit(bootstrap_history)

    # Shared image hash for duplicate evidence demonstration
    shared_duplicate_image_url = SAMPLE_IMAGE_PLACEHOLDERS[0]
    shared_duplicate_image_hash = compute_sha256_hash(shared_duplicate_image_url.encode("utf-8"))

    # 6. Seed Dedicated Worked Case: MP-2024-8842
    # Sanctioned = ₹25,00,000, Expenditure = ₹22,50,000, Payment = 90%, Physical = 35%, Mismatch = 55%, Delay = 6 mo, GPS deviation = 4.2 km
    sanctioned_lat_8842 = 25.3176
    sanctioned_lon_8842 = 82.9739
    actual_lat_8842 = 25.34428
    actual_lon_8842 = 83.00341
    geo_dist_8842 = calculate_haversine_distance(sanctioned_lat_8842, sanctioned_lon_8842, actual_lat_8842, actual_lon_8842) # ~4.2 km

    worked_analysis = ml_engine.analyze_project(
        title="Construction of Community Center & Skill Training Hub, Ward 14",
        description="Construction of 2-storey multi-purpose community center and women skill development center in Ward 14 Chowk area under DRDA Varanasi supervision.",
        category="Community Halls & Libraries",
        sanctioned_amount=2500000.00,
        expenditure_amount=2250000.00,
        start_date="2024-01-15",
        target_completion_date="2024-07-15",
        contractor_name=apex_contractor.name,
        contractor_gstin=apex_contractor.gstin,
        district_name="Varanasi",
        physical_progress=35.0,
        sanctioned_lat=sanctioned_lat_8842,
        sanctioned_lon=sanctioned_lon_8842,
        actual_lat=actual_lat_8842,
        actual_lon=actual_lon_8842,
        has_duplicate_evidence=True,
        delay_months=6.0
    )

    worked_project = Project(
        project_code="MP-2024-8842",
        mp_id=varanasi_mp.id,
        district_id=varanasi_dist.id,
        contractor_id=apex_contractor.id,
        title="Construction of Community Center & Skill Training Hub, Ward 14",
        description="Construction of 2-storey multi-purpose community center and women skill development center in Ward 14 Chowk area under DRDA Varanasi supervision.",
        category="Community Halls & Libraries",
        sanctioned_amount=2500000.00,
        expenditure_amount=2250000.00,
        start_date=date(2024, 1, 15),
        target_completion_date=date(2024, 7, 15),
        actual_completion_date=None,
        status="Suspended",
        location="Ward 14, Chowk Area, Varanasi",
        physical_progress=35.0,
        payment_progress=90.0,
        progress_mismatch=55.0,
        sanctioned_latitude=sanctioned_lat_8842,
        sanctioned_longitude=sanctioned_lon_8842,
        actual_latitude=actual_lat_8842,
        actual_longitude=actual_lon_8842,
        geo_distance_meters=round(geo_dist_8842, 1),
        geo_anomaly_flag=True,
        cost_score=worked_analysis["cost_score"],
        timeline_score=worked_analysis["timeline_score"],
        payment_score=worked_analysis["payment_score"],
        geo_score=worked_analysis["geo_score"],
        duplicate_score=worked_analysis["duplicate_score"],
        matched_proposal_title=worked_analysis.get("matched_project"),
        duplicate_similarity_ratio=float(worked_analysis.get("similarity_score", 0.0)) / 100.0,
        risk_score=worked_analysis["final_risk_score"],
        severity=worked_analysis["severity"],
        is_flagged=True,
        review_status="AI_FLAGGED",
        review_remarks="Flagged for immediate on-site verification: 90% payment disbursed against 35% physical progress and 4.2 km GPS site deviation.",
        created_at=datetime(2024, 1, 15, 10, 0, 0)
    )
    db_session.add(worked_project)
    await db_session.flush()

    # Milestones for MP-2024-8842
    m1 = Milestone(project_id=worked_project.id, name="Foundation & Plinth", planned_start_date=date(2024, 1, 15), planned_end_date=date(2024, 3, 1), actual_start_date=date(2024, 1, 20), actual_end_date=date(2024, 3, 10), completion_percentage=100.0, status="Completed")
    m2 = Milestone(project_id=worked_project.id, name="RCC Pillar & Brick Masonry", planned_start_date=date(2024, 3, 2), planned_end_date=date(2024, 5, 1), actual_start_date=date(2024, 3, 15), actual_end_date=None, completion_percentage=40.0, status="Delayed")
    m3 = Milestone(project_id=worked_project.id, name="Roofing, Plastering & Electricals", planned_start_date=date(2024, 5, 2), planned_end_date=date(2024, 6, 20), actual_start_date=None, actual_end_date=None, completion_percentage=0.0, status="Delayed")
    m4 = Milestone(project_id=worked_project.id, name="Finishing & Handover", planned_start_date=date(2024, 6, 21), planned_end_date=date(2024, 7, 15), actual_start_date=None, actual_end_date=None, completion_percentage=0.0, status="Pending")
    db_session.add_all([m1, m2, m3, m4])

    # Evidence for MP-2024-8842 (with duplicate image flag)
    ev1 = Evidence(
        project_id=worked_project.id,
        image_path=shared_duplicate_image_url,
        image_hash=shared_duplicate_image_hash,
        latitude=actual_lat_8842,
        longitude=actual_lon_8842,
        uploaded_by="Junior Engineer (DRDA)",
        description="Foundation and column reinforcement photo submitted for Tranche 2 release.",
        is_duplicate_flag=True
    )
    ev2 = Evidence(
        project_id=worked_project.id,
        image_path=SAMPLE_IMAGE_PLACEHOLDERS[3],
        image_hash=compute_sha256_hash(SAMPLE_IMAGE_PLACEHOLDERS[3].encode("utf-8")),
        latitude=actual_lat_8842,
        longitude=actual_lon_8842,
        uploaded_by="Field Inspector (MoSPI)",
        description="GPS geotagged survey photo showing incomplete single-story frame at 4.2 km coordinate offset.",
        is_duplicate_flag=False
    )
    db_session.add_all([ev1, ev2])

    # Disbursements for MP-2024-8842 (3 tranches totaling ₹22.5 Lakhs)
    db_session.add(FundDisbursement(project_id=worked_project.id, disbursement_date=date(2024, 1, 25), amount=750000.0, tranche_number=1, remarks="Mobilization advance (30%) released."))
    db_session.add(FundDisbursement(project_id=worked_project.id, disbursement_date=date(2024, 3, 20), amount=1000000.0, tranche_number=2, remarks="Tranche 2 released after plinth inspection."))
    db_session.add(FundDisbursement(project_id=worked_project.id, disbursement_date=date(2024, 5, 10), amount=500000.0, tranche_number=3, remarks="Tranche 3 advance released."))

    # Anomaly logs for MP-2024-8842
    for factor in worked_analysis["risk_factors"]:
        db_session.add(AnomalyLog(
            project_id=worked_project.id,
            anomaly_type=factor["name"],
            severity=factor["severity"],
            confidence_score=round(factor["score"], 1),
            details=factor["description"],
            llm_explanation=None
        ))

    # Tamper-Evident Hash Chained Audit Log for MP-2024-8842
    init_prev_hash = "0" * 64
    content1 = f"{init_prev_hash}|Project|{worked_project.id}|PROJECT_CREATED|2024-01-15T10:00:00|Initial proposal approved and sanctioned."
    hash1 = hashlib.sha256(content1.encode("utf-8")).hexdigest()
    audit1 = AuditLog(
        project_id=worked_project.id,
        username="DRDA Admin",
        action="PROJECT_CREATED",
        entity_type="Project",
        entity_id=worked_project.id,
        remarks="Initial proposal approved and sanctioned.",
        timestamp=datetime(2024, 1, 15, 10, 0, 0),
        previous_hash=init_prev_hash,
        record_hash=hash1
    )

    content2 = f"{hash1}|Project|{worked_project.id}|AI_ANOMALY_FLAGGED|2024-06-01T14:30:00|Automated SIH Risk Engine flagged 90% disbursement vs 35% physical progress and 4.2 km GPS distance anomaly."
    hash2 = hashlib.sha256(content2.encode("utf-8")).hexdigest()
    audit2 = AuditLog(
        project_id=worked_project.id,
        username="AI Risk Engine",
        action="AI_ANOMALY_FLAGGED",
        entity_type="Project",
        entity_id=worked_project.id,
        remarks="Automated SIH Risk Engine flagged 90% disbursement vs 35% physical progress and 4.2 km GPS distance anomaly.",
        timestamp=datetime(2024, 6, 1, 14, 30, 0),
        previous_hash=hash1,
        record_hash=hash2
    )
    db_session.add_all([audit1, audit2])

    # Notification for MP-2024-8842
    db_session.add(Notification(
        user_id=users_data[0].id,
        project_id=worked_project.id,
        title="Critical Anomaly Flagged (MP-2024-8842)",
        message="MP-2024-8842 flagged with Critical Risk: 90% payment vs 35% physical progress (55% mismatch) and 4.2 km site location deviation. Requires review.",
        severity="CRITICAL",
        is_read=False
    ))

    # 7. Generate 1,050+ Realistic Synthetic Projects
    start_base_date = date(2024, 1, 1)
    historical_for_ml = []
    historical_for_ml.append({
        "title": worked_project.title,
        "description": worked_project.description,
        "category": worked_project.category,
        "sanctioned_amount": worked_project.sanctioned_amount,
        "expenditure_amount": worked_project.expenditure_amount,
        "start_date": str(worked_project.start_date),
        "target_completion_date": str(worked_project.target_completion_date)
    })

    duplicate_title_text = "Construction of Concrete Drain and CC Road in Ward 14 Chowk Area"

    total_target = 1050
    for i in range(1, total_target + 1):
        mp = random.choice(mps)
        dist = random.choice(districts)
        contractor = random.choice(contractors)
        category = random.choice(CATEGORIES)
        location = f"Village/Ward {random.randint(1, 45)}, {dist.name}"
        p_code = f"MPLADS-{i:05d}"

        sanctioned = float(random.randint(5, 75) * 100000) # 5L to 75L
        dist_coords = DISTRICT_COORDINATES.get(dist.name, (25.3176, 82.9739))
        s_lat = dist_coords[0] + random.uniform(-0.04, 0.04)
        s_lon = dist_coords[1] + random.uniform(-0.04, 0.04)

        start_dt = start_base_date + timedelta(days=random.randint(0, 200))
        target_dt = start_dt + timedelta(days=random.randint(90, 240))

        # Decide anomaly scenario
        is_anomaly_case = (i % 7 == 0) or contractor.blacklisted_status
        anomaly_scenario = random.choice(["cost_overrun", "payment_mismatch", "geo_anomaly", "duplicate_project", "timeline_delay", "duplicate_evidence"]) if is_anomaly_case else "normal"

        has_dup_ev = False
        if anomaly_scenario == "cost_overrun":
            expenditure = round(sanctioned * random.uniform(1.45, 1.85), 2)
            payment_pct = (expenditure / sanctioned * 100.0)
            physical_pct = round(random.uniform(70.0, 95.0), 1)
            act_lat = s_lat + random.uniform(-0.002, 0.002)
            act_lon = s_lon + random.uniform(-0.002, 0.002)
            delay_m = random.uniform(0.5, 2.0)
            title = random.choice(PROJECT_TITLE_TEMPLATES).format(location=location)

        elif anomaly_scenario == "payment_mismatch":
            expenditure = round(sanctioned * random.uniform(0.85, 0.98), 2)
            payment_pct = (expenditure / sanctioned * 100.0)
            physical_pct = round(random.uniform(25.0, 45.0), 1) # 45-60% mismatch
            act_lat = s_lat + random.uniform(-0.002, 0.002)
            act_lon = s_lon + random.uniform(-0.002, 0.002)
            delay_m = random.uniform(1.0, 4.0)
            title = random.choice(PROJECT_TITLE_TEMPLATES).format(location=location)

        elif anomaly_scenario == "geo_anomaly":
            expenditure = round(sanctioned * random.uniform(0.80, 1.05), 2)
            payment_pct = (expenditure / sanctioned * 100.0)
            physical_pct = round(random.uniform(50.0, 80.0), 1)
            # Offset actual coordinates by ~3.5 to 6.0 km
            act_lat = s_lat + random.uniform(0.035, 0.060)
            act_lon = s_lon + random.uniform(0.035, 0.060)
            delay_m = 1.0
            title = random.choice(PROJECT_TITLE_TEMPLATES).format(location=location)

        elif anomaly_scenario == "duplicate_project":
            expenditure = round(sanctioned * random.uniform(0.85, 1.05), 2)
            payment_pct = (expenditure / sanctioned * 100.0)
            physical_pct = round(random.uniform(60.0, 90.0), 1)
            act_lat = s_lat + random.uniform(-0.002, 0.002)
            act_lon = s_lon + random.uniform(-0.002, 0.002)
            delay_m = 0.5
            title = duplicate_title_text

        elif anomaly_scenario == "duplicate_evidence":
            expenditure = round(sanctioned * random.uniform(0.85, 1.10), 2)
            payment_pct = (expenditure / sanctioned * 100.0)
            physical_pct = round(random.uniform(50.0, 75.0), 1)
            act_lat = s_lat + random.uniform(-0.002, 0.002)
            act_lon = s_lon + random.uniform(-0.002, 0.002)
            delay_m = 1.5
            has_dup_ev = True
            title = random.choice(PROJECT_TITLE_TEMPLATES).format(location=location)

        elif anomaly_scenario == "timeline_delay":
            expenditure = round(sanctioned * random.uniform(0.60, 0.85), 2)
            payment_pct = (expenditure / sanctioned * 100.0)
            physical_pct = round(random.uniform(30.0, 50.0), 1)
            act_lat = s_lat + random.uniform(-0.002, 0.002)
            act_lon = s_lon + random.uniform(-0.002, 0.002)
            delay_m = random.uniform(5.5, 9.0) # 6+ months delay
            title = random.choice(PROJECT_TITLE_TEMPLATES).format(location=location)

        else: # Normal baseline project
            expenditure = round(sanctioned * random.uniform(0.75, 0.95), 2)
            payment_pct = (expenditure / sanctioned * 100.0)
            physical_pct = round(payment_pct * random.uniform(0.92, 1.05), 1)
            act_lat = s_lat + random.uniform(-0.001, 0.001)
            act_lon = s_lon + random.uniform(-0.001, 0.001)
            delay_m = 0.0
            title = random.choice(PROJECT_TITLE_TEMPLATES).format(location=location)

        # Haversine distance
        geo_dist = calculate_haversine_distance(s_lat, s_lon, act_lat, act_lon)
        is_geo_anom = geo_dist > 500.0

        # Run SIH ML risk pipeline
        analysis = ml_engine.analyze_project(
            title=title,
            description=f"MPLAD scheme infrastructure project for {title} under DRDA {dist.name}.",
            category=category,
            sanctioned_amount=sanctioned,
            expenditure_amount=expenditure,
            start_date=str(start_dt),
            target_completion_date=str(target_dt),
            contractor_name=contractor.name,
            contractor_gstin=contractor.gstin,
            district_name=dist.name,
            physical_progress=physical_pct,
            sanctioned_lat=s_lat,
            sanctioned_lon=s_lon,
            actual_lat=act_lat,
            actual_lon=act_lon,
            is_contractor_blacklisted=contractor.blacklisted_status,
            has_duplicate_evidence=has_dup_ev,
            delay_months=delay_m
        )

        status_val = "Completed" if physical_pct >= 95.0 else ("Suspended" if analysis["severity"] in ["CRITICAL", "HIGH"] else "In Progress")
        if analysis["severity"] == "CRITICAL":
            review_stat = random.choice(["AI_FLAGGED", "AI_FLAGGED", "UNDER_REVIEW", "CLARIFICATION_REQUIRED"])
        elif analysis["severity"] == "HIGH":
            review_stat = random.choice(["AI_FLAGGED", "UNDER_REVIEW", "VERIFIED", "CLARIFICATION_REQUIRED"])
        elif analysis["severity"] == "MEDIUM":
            review_stat = random.choice(["AI_FLAGGED", "UNDER_REVIEW", "DISMISSED", "RESOLVED"])
        else:
            review_stat = random.choice(["RESOLVED", "DISMISSED", "VERIFIED"])

        proj = Project(
            project_code=p_code,
            mp_id=mp.id,
            district_id=dist.id,
            contractor_id=contractor.id,
            title=title,
            description=f"MPLAD scheme infrastructure project for {title} under DRDA {dist.name}.",
            category=category,
            sanctioned_amount=sanctioned,
            expenditure_amount=expenditure,
            start_date=start_dt,
            target_completion_date=target_dt,
            actual_completion_date=target_dt if status_val == "Completed" else None,
            status=status_val,
            location=location,
            physical_progress=physical_pct,
            payment_progress=round(payment_pct, 1),
            progress_mismatch=round(payment_pct - physical_pct, 1),
            sanctioned_latitude=round(s_lat, 6),
            sanctioned_longitude=round(s_lon, 6),
            actual_latitude=round(act_lat, 6),
            actual_longitude=round(act_lon, 6),
            geo_distance_meters=round(geo_dist, 1),
            geo_anomaly_flag=is_geo_anom,
            cost_score=analysis["cost_score"],
            timeline_score=analysis["timeline_score"],
            payment_score=analysis["payment_score"],
            geo_score=analysis["geo_score"],
            duplicate_score=analysis["duplicate_score"],
            matched_proposal_title=analysis.get("matched_project"),
            duplicate_similarity_ratio=float(analysis.get("similarity_score", 0.0)) / 100.0,
            risk_score=analysis["final_risk_score"],
            severity=analysis["severity"],
            is_flagged=analysis["is_flagged"],
            review_status=review_stat,
            review_remarks=analysis["ai_summary"] if analysis["is_flagged"] else None
        )
        db_session.add(proj)
        await db_session.flush()

        mp.utilized_budget = float(mp.utilized_budget or 0) + expenditure

        # Add 3 fund disbursements
        t1 = round(expenditure * 0.35, 2)
        t2 = round(expenditure * 0.40, 2)
        t3 = round(expenditure * 0.25, 2)
        db_session.add(FundDisbursement(project_id=proj.id, disbursement_date=start_dt + timedelta(days=20), amount=t1, tranche_number=1, remarks="Tranche 1 advance."))
        db_session.add(FundDisbursement(project_id=worked_project.id if False else proj.id, disbursement_date=start_dt + timedelta(days=60), amount=t2, tranche_number=2, remarks="Tranche 2 progress payment."))
        if expenditure > (t1 + t2):
            db_session.add(FundDisbursement(project_id=proj.id, disbursement_date=start_dt + timedelta(days=100), amount=t3, tranche_number=3, remarks="Tranche 3 release."))

        # Add Milestones
        db_session.add(Milestone(project_id=proj.id, name="Preliminary & Excavation", planned_start_date=start_dt, planned_end_date=start_dt + timedelta(days=30), completion_percentage=min(physical_pct * 2, 100.0), status="Completed" if physical_pct >= 50 else "In Progress"))
        db_session.add(Milestone(project_id=proj.id, name="Civil Construction & Framing", planned_start_date=start_dt + timedelta(days=31), planned_end_date=start_dt + timedelta(days=90), completion_percentage=max(0.0, min((physical_pct - 30.0) * 1.5, 100.0)), status="Completed" if physical_pct >= 90 else ("In Progress" if physical_pct >= 30 else "Pending")))
        db_session.add(Milestone(project_id=proj.id, name="Finishing & Commissioning", planned_start_date=start_dt + timedelta(days=91), planned_end_date=target_dt, completion_percentage=max(0.0, physical_pct - 70.0) if physical_pct > 70 else 0.0, status="Completed" if physical_pct >= 100 else "Pending"))

        # Add Evidence Photo
        img_url = shared_duplicate_image_url if has_dup_ev else random.choice(SAMPLE_IMAGE_PLACEHOLDERS)
        img_hash = shared_duplicate_image_hash if has_dup_ev else compute_sha256_hash(f"{img_url}_{i}".encode("utf-8"))
        db_session.add(Evidence(
            project_id=proj.id,
            image_path=img_url,
            image_hash=img_hash,
            latitude=act_lat,
            longitude=act_lon,
            uploaded_by="District Field Inspector",
            description=f"Site inspection photo for {proj.project_code}.",
            is_duplicate_flag=has_dup_ev
        ))

        # Add Anomaly Logs for flagged projects
        if analysis["is_flagged"]:
            for signal in analysis["risk_factors"][:2]:
                db_session.add(AnomalyLog(
                    project_id=proj.id,
                    anomaly_type=signal["name"],
                    severity=signal["severity"],
                    confidence_score=round(signal["score"], 1),
                    details=signal["description"]
                ))

            # Add Audit Log
            p_hash0 = "0" * 64
            p_payload = f"{p_hash0}|Project|{proj.id}|AI_ANOMALY_FLAGGED|{datetime.utcnow().isoformat()}|{analysis['severity']} anomaly score {analysis['final_risk_score']}/100."
            p_hash1 = hashlib.sha256(p_payload.encode("utf-8")).hexdigest()
            db_session.add(AuditLog(
                project_id=proj.id,
                username="AI Risk Engine",
                action="AI_ANOMALY_FLAGGED",
                entity_type="Project",
                entity_id=proj.id,
                remarks=f"{analysis['severity']} anomaly score {analysis['final_risk_score']}/100.",
                timestamp=datetime.utcnow(),
                previous_hash=p_hash0,
                record_hash=p_hash1
            ))

            if analysis["severity"] == "CRITICAL" and (i % 3 == 0):
                db_session.add(Notification(
                    project_id=proj.id,
                    title=f"Critical Anomaly Detected ({p_code})",
                    message=f"High risk score {analysis['final_risk_score']}/100 calculated for {proj.title}.",
                    severity="CRITICAL"
                ))

        historical_for_ml.append({
            "title": title,
            "description": f"MPLAD scheme infrastructure project for {title} under DRDA {dist.name}.",
            "category": category,
            "sanctioned_amount": sanctioned,
            "expenditure_amount": expenditure,
            "start_date": str(start_dt),
            "target_completion_date": str(target_dt)
        })

    await db_session.commit()

    # Fit ML models with complete dataset
    ml_engine.fit(historical_for_ml)
    print(f"[Seed Script] Successfully populated {total_target + 1} projects (including worked case MP-2024-8842) and trained ML models.")
    return total_target + 1

async def main():
    print("[Seed Script] Starting PostgreSQL / SQLite seeding process...")
    await init_db()
    async with AsyncSessionLocal() as session:
        count = await seed_database_internal(session, force_if_empty=False)
        print(f"[Seed Script] Completed! Seeded {count} records into MPLADS database.")

if __name__ == "__main__":
    asyncio.run(main())

