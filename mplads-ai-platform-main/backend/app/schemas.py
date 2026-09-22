from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Any, Dict
from datetime import date, datetime

class UserSchema(BaseModel):
    id: int
    username: str
    full_name: str
    role: str  # ADMIN, DISTRICT_OFFICER, AUDITOR
    district_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserLoginRequest(BaseModel):
    username: str
    password: str


class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserSchema


class MPSchema(BaseModel):
    id: int
    name: str
    constituency: str
    state: str
    party: str
    allocated_budget: float
    utilized_budget: float

    class Config:
        from_attributes = True


class DistrictSchema(BaseModel):
    id: int
    name: str
    state: str
    nodal_agency: str
    risk_score: float

    class Config:
        from_attributes = True


class ContractorSchema(BaseModel):
    id: int
    name: str
    gstin: str
    rating: float
    blacklisted_status: bool
    registered_date: date

    class Config:
        from_attributes = True


class FundDisbursementSchema(BaseModel):
    id: int
    project_id: int
    disbursement_date: date
    amount: float
    tranche_number: int
    remarks: Optional[str] = None

    class Config:
        from_attributes = True


class MilestoneSchema(BaseModel):
    id: int
    project_id: int
    name: str
    planned_start_date: date
    planned_end_date: date
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    completion_percentage: float = 0.0
    status: str = "Pending"

    class Config:
        from_attributes = True


class EvidenceSchema(BaseModel):
    id: int
    project_id: int
    image_path: str
    image_hash: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    uploaded_at: datetime
    uploaded_by: str = "Field Inspector"
    description: Optional[str] = None
    is_duplicate_flag: bool = False

    class Config:
        from_attributes = True


class EvidenceCreateRequest(BaseModel):
    image_path: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    uploaded_by: Optional[str] = "Field Inspector"


class AuditLogSchema(BaseModel):
    id: int
    project_id: Optional[int] = None
    user_id: Optional[int] = None
    username: str = "System"
    action: str
    entity_type: str = "Project"
    entity_id: int
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    remarks: Optional[str] = None
    timestamp: datetime
    previous_hash: str
    record_hash: str

    class Config:
        from_attributes = True


class NotificationSchema(BaseModel):
    id: int
    user_id: Optional[int] = None
    project_id: Optional[int] = None
    title: str
    message: str
    severity: str = "LOW"
    is_read: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class AnomalyLogSchema(BaseModel):
    id: int
    project_id: int
    anomaly_type: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    confidence_score: float
    detected_at: datetime
    details: str
    llm_explanation: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectSchema(BaseModel):
    id: int
    project_code: str
    mp_id: int
    district_id: int
    contractor_id: int
    title: str
    description: Optional[str] = None
    category: str
    sanctioned_amount: float
    expenditure_amount: float
    start_date: date
    target_completion_date: date
    actual_completion_date: Optional[date] = None
    status: str
    location: str

    # 1. Progress & Mismatch
    physical_progress: float = 0.0
    payment_progress: float = 0.0
    progress_mismatch: float = 0.0

    # 2. Geospatial
    sanctioned_latitude: Optional[float] = None
    sanctioned_longitude: Optional[float] = None
    actual_latitude: Optional[float] = None
    actual_longitude: Optional[float] = None
    geo_distance_meters: float = 0.0
    geo_anomaly_flag: bool = False

    # 3. SIH Composite Risk Scores
    cost_score: float = 0.0
    timeline_score: float = 0.0
    payment_score: float = 0.0
    geo_score: float = 0.0
    duplicate_score: float = 0.0
    matched_proposal_title: Optional[str] = None
    duplicate_similarity_ratio: float = 0.0
    risk_score: float = 0.0
    final_risk_score: Optional[float] = None
    severity: str = "LOW"

    # 4. Human-in-the-Loop Workflow
    is_flagged: bool = False
    review_status: str = "AI_FLAGGED"
    review_remarks: Optional[str] = None
    created_at: datetime

    # Relationships & Join labels
    mp_name: Optional[str] = None
    district_name: Optional[str] = None
    contractor_name: Optional[str] = None
    anomaly_logs: List[AnomalyLogSchema] = []
    milestones: List[MilestoneSchema] = []
    evidence_items: List[EvidenceSchema] = []
    audit_logs: List[AuditLogSchema] = []

    class Config:
        from_attributes = True

    @model_validator(mode="after")
    def alias_final_risk_score(self):
        if self.final_risk_score is None:
            self.final_risk_score = self.risk_score
        return self


class ReviewActionRequest(BaseModel):
    action: str = Field(..., example="VERIFY") # REVIEW, VERIFY, CLARIFICATION, DISMISS, RESOLVE
    remarks: str = Field(..., example="Physical audit completed; verified 4.2 km coordinate discrepancy.")
    username: Optional[str] = "Admin Officer"


class ClarificationRequest(BaseModel):
    remarks: str = Field(..., example="Request nodal agency clarify 55% payment-progress mismatch.")
    requested_to: Optional[str] = "District Nodal Agency"
    username: Optional[str] = "District Auditor"


class RiskFactorDetail(BaseModel):
    name: str
    severity: str
    score: float
    description: str


class ProjectAnalyzeRequest(BaseModel):
    title: str = Field(..., example="Construction of Community Center & Skill Training Hub, Ward 14")
    category: str = Field("Community Halls & Libraries", example="Community Halls & Libraries")
    sanctioned_amount: float = Field(2500000.0, example=2500000.0)
    expenditure_amount: float = Field(2250000.0, example=2250000.0)
    physical_progress: Optional[float] = Field(35.0, example=35.0)
    start_date: date = Field(..., example="2024-01-10")
    target_completion_date: date = Field(..., example="2024-07-10")
    contractor_name: str = Field("Apex Infrastructure Pvt Ltd", example="Apex Infrastructure Pvt Ltd")
    contractor_gstin: str = Field("07AAAAA0000A1Z5", example="07AAAAA0000A1Z5")
    district_name: str = Field("Varanasi", example="Varanasi")
    location: str = Field("Chowk Area, Ward 14, Varanasi", example="Chowk Area, Ward 14, Varanasi")
    sanctioned_latitude: Optional[float] = Field(25.3176, example=25.3176)
    sanctioned_longitude: Optional[float] = Field(82.9739, example=82.9739)
    actual_latitude: Optional[float] = Field(25.3443, example=25.3443)
    actual_longitude: Optional[float] = Field(83.0034, example=83.0034)
    delay_months: Optional[float] = Field(6.0, example=6.0)
    mp_name: Optional[str] = Field("Dr. Rajesh Sharma", example="Dr. Rajesh Sharma")


class ProjectAnalyzeResponse(BaseModel):
    cost_score: float
    timeline_score: float
    payment_score: float
    geo_score: float
    duplicate_score: float
    final_risk_score: float
    risk_score: float
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    risk_level: str
    is_flagged: bool
    physical_progress: float
    payment_progress: float
    progress_mismatch: float
    geo_distance_meters: float
    geo_anomaly_flag: bool
    recommendation: str
    risk_factors: List[RiskFactorDetail]
    ai_summary: str
    matched_project: Optional[str] = None
    similarity_score: Optional[float] = 0.0
    duplicate_status: Optional[str] = "NORMAL"
    model_used: Optional[str] = "Sentence-BERT (all-MiniLM-L6-v2)"


class KPISummaryResponse(BaseModel):
    total_sanctioned_funds: float
    total_expenditure: float
    suspended_fraud_value: float
    total_projects: int
    flagged_projects_count: int
    critical_projects_count: int
    high_risk_projects_count: int
    top_5_percent_count: int
    payment_mismatch_count: int
    geospatial_anomaly_count: int
    duplicate_evidence_count: int
    duplicate_project_count: int
    timeline_delay_count: int
    cases_under_review_count: int
    cases_resolved_count: int
    high_risk_ratio: float
    anomaly_type_breakdown: List[dict]
    severity_distribution: List[dict]
    category_variance: List[dict]
    district_risk_rankings: List[dict]
    monthly_fund_flow: List[dict]
    risk_factor_distribution: Optional[List[dict]] = []


class ExecutiveExplanationResponse(BaseModel):
    project_id: int
    project_title: str
    risk_score: float
    executive_summary: str
    generated_at: datetime

