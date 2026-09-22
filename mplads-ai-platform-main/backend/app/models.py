from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Numeric, Boolean, Date, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="AUDITOR")  # ADMIN, DISTRICT_OFFICER, AUDITOR
    district_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MP(Base):
    __tablename__ = "mps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    constituency = Column(String(255), nullable=False)
    state = Column(String(255), nullable=False)
    party = Column(String(100), nullable=False)
    allocated_budget = Column(Numeric(15, 2), default=50000000.00)
    utilized_budget = Column(Numeric(15, 2), default=0.00)
    created_at = Column(DateTime, default=datetime.utcnow)

    projects = relationship("Project", back_populates="mp", cascade="all, delete-orphan")


class District(Base):
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    state = Column(String(255), nullable=False)
    nodal_agency = Column(String(255), nullable=False)
    risk_score = Column(Numeric(5, 2), default=0.00)

    projects = relationship("Project", back_populates="district", cascade="all, delete-orphan")


class Contractor(Base):
    __tablename__ = "contractors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    gstin = Column(String(15), unique=True, nullable=False, index=True)
    rating = Column(Numeric(3, 2), default=4.00)
    blacklisted_status = Column(Boolean, default=False)
    registered_date = Column(Date, default=date.today)

    projects = relationship("Project", back_populates="contractor", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    project_code = Column(String(50), unique=True, nullable=False, index=True)
    mp_id = Column(Integer, ForeignKey("mps.id", ondelete="CASCADE"), nullable=False)
    district_id = Column(Integer, ForeignKey("districts.id", ondelete="CASCADE"), nullable=False)
    contractor_id = Column(Integer, ForeignKey("contractors.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, index=True)
    sanctioned_amount = Column(Numeric(15, 2), nullable=False)
    expenditure_amount = Column(Numeric(15, 2), default=0.00)
    start_date = Column(Date, nullable=False)
    target_completion_date = Column(Date, nullable=False)
    actual_completion_date = Column(Date, nullable=True)
    status = Column(String(50), default="In Progress")
    location = Column(String(255), nullable=False)

    # 1. Progress Metrics
    physical_progress = Column(Float, default=0.0)
    payment_progress = Column(Float, default=0.0)
    progress_mismatch = Column(Float, default=0.0)

    # 2. Geospatial Verification
    sanctioned_latitude = Column(Float, nullable=True)
    sanctioned_longitude = Column(Float, nullable=True)
    actual_latitude = Column(Float, nullable=True)
    actual_longitude = Column(Float, nullable=True)
    geo_distance_meters = Column(Float, default=0.0)
    geo_anomaly_flag = Column(Boolean, default=False, index=True)

    # 3. SIH Composite Risk Scores (Normalized 0-100)
    cost_score = Column(Float, default=0.0)
    timeline_score = Column(Float, default=0.0)
    payment_score = Column(Float, default=0.0)
    geo_score = Column(Float, default=0.0)
    duplicate_score = Column(Float, default=0.0)
    matched_proposal_title = Column(String(500), nullable=True)
    duplicate_similarity_ratio = Column(Float, default=0.0)
    risk_score = Column(Numeric(5, 2), default=0.00, index=True)
    severity = Column(String(20), default="LOW", index=True)  # LOW, MEDIUM, HIGH, CRITICAL

    # 4. Human-In-The-Loop Case Review Workflow
    is_flagged = Column(Boolean, default=False, index=True)
    review_status = Column(String(50), default="AI_FLAGGED", index=True)  # AI_FLAGGED, UNDER_REVIEW, CLARIFICATION_REQUIRED, VERIFIED, DISMISSED, RESOLVED
    review_remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    mp = relationship("MP", back_populates="projects")
    district = relationship("District", back_populates="projects")
    contractor = relationship("Contractor", back_populates="projects")
    fund_disbursements = relationship("FundDisbursement", back_populates="project", cascade="all, delete-orphan")
    anomaly_logs = relationship("AnomalyLog", back_populates="project", cascade="all, delete-orphan")
    milestones = relationship("Milestone", back_populates="project", cascade="all, delete-orphan")
    evidence_items = relationship("Evidence", back_populates="project", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="project", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="project", cascade="all, delete-orphan")


class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    planned_start_date = Column(Date, nullable=False)
    planned_end_date = Column(Date, nullable=False)
    actual_start_date = Column(Date, nullable=True)
    actual_end_date = Column(Date, nullable=True)
    completion_percentage = Column(Float, default=0.0)
    status = Column(String(50), default="Pending")  # Pending, In Progress, Completed, Delayed

    project = relationship("Project", back_populates="milestones")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    image_path = Column(String(500), nullable=False)
    image_hash = Column(String(64), nullable=False, index=True)  # SHA-256
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(String(100), default="Field Inspector")
    description = Column(Text, nullable=True)
    is_duplicate_flag = Column(Boolean, default=False, index=True)

    project = relationship("Project", back_populates="evidence_items")


class FundDisbursement(Base):
    __tablename__ = "fund_disbursements"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    disbursement_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    tranche_number = Column(Integer, nullable=False)
    remarks = Column(Text, nullable=True)

    project = relationship("Project", back_populates="fund_disbursements")


class AnomalyLog(Base):
    __tablename__ = "anomaly_logs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    anomaly_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False, index=True)  # CRITICAL, HIGH, MEDIUM, LOW
    confidence_score = Column(Numeric(5, 2), nullable=False)
    detected_at = Column(DateTime, default=datetime.utcnow)
    details = Column(Text, nullable=False)
    llm_explanation = Column(Text, nullable=True)

    project = relationship("Project", back_populates="anomaly_logs")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(Integer, nullable=True)
    username = Column(String(100), default="System")
    action = Column(String(100), nullable=False)  # PROJECT_VIEWED, STATUS_CHANGED, CLARIFICATION_REQUESTED, PROJECT_VERIFIED, PROJECT_DISMISSED, PROJECT_RESOLVED, EVIDENCE_ADDED
    entity_type = Column(String(50), nullable=False, default="Project")
    entity_id = Column(Integer, nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    remarks = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    previous_hash = Column(String(64), nullable=False, default="0"*64)
    record_hash = Column(String(64), nullable=False)

    project = relationship("Project", back_populates="audit_logs")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="LOW")  # CRITICAL, HIGH, MEDIUM, LOW
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="notifications")
