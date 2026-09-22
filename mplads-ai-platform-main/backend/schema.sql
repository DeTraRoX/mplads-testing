-- PostgreSQL Schema (3NF) for MPLAD Scheme AI Detection Platform

DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS evidence CASCADE;
DROP TABLE IF EXISTS milestones CASCADE;
DROP TABLE IF EXISTS anomaly_logs CASCADE;
DROP TABLE IF EXISTS fund_disbursements CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS contractors CASCADE;
DROP TABLE IF EXISTS districts CASCADE;
DROP TABLE IF EXISTS mps CASCADE;
DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'AUDITOR',
    district_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE mps (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    constituency VARCHAR(255) NOT NULL,
    state VARCHAR(255) NOT NULL,
    party VARCHAR(100) NOT NULL,
    allocated_budget NUMERIC(15, 2) DEFAULT 50000000.00,
    utilized_budget NUMERIC(15, 2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE districts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    state VARCHAR(255) NOT NULL,
    nodal_agency VARCHAR(255) NOT NULL,
    risk_score NUMERIC(5, 2) DEFAULT 0.00
);

CREATE TABLE contractors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    gstin VARCHAR(15) UNIQUE NOT NULL,
    rating NUMERIC(3, 2) DEFAULT 4.00,
    blacklisted_status BOOLEAN DEFAULT FALSE,
    registered_date DATE NOT NULL
);

CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    project_code VARCHAR(50) UNIQUE NOT NULL,
    mp_id INTEGER REFERENCES mps(id) ON DELETE CASCADE,
    district_id INTEGER REFERENCES districts(id) ON DELETE CASCADE,
    contractor_id INTEGER REFERENCES contractors(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,
    sanctioned_amount NUMERIC(15, 2) NOT NULL,
    expenditure_amount NUMERIC(15, 2) DEFAULT 0.00,
    start_date DATE NOT NULL,
    target_completion_date DATE NOT NULL,
    actual_completion_date DATE,
    status VARCHAR(50) NOT NULL DEFAULT 'In Progress',
    location VARCHAR(255) NOT NULL,
    physical_progress DOUBLE PRECISION DEFAULT 0.0,
    payment_progress DOUBLE PRECISION DEFAULT 0.0,
    progress_mismatch DOUBLE PRECISION DEFAULT 0.0,
    sanctioned_latitude DOUBLE PRECISION,
    sanctioned_longitude DOUBLE PRECISION,
    actual_latitude DOUBLE PRECISION,
    actual_longitude DOUBLE PRECISION,
    geo_distance_meters DOUBLE PRECISION DEFAULT 0.0,
    geo_anomaly_flag BOOLEAN DEFAULT FALSE,
    cost_score DOUBLE PRECISION DEFAULT 0.0,
    timeline_score DOUBLE PRECISION DEFAULT 0.0,
    payment_score DOUBLE PRECISION DEFAULT 0.0,
    geo_score DOUBLE PRECISION DEFAULT 0.0,
    duplicate_score DOUBLE PRECISION DEFAULT 0.0,
    matched_proposal_title VARCHAR(500),
    duplicate_similarity_ratio DOUBLE PRECISION DEFAULT 0.0,
    risk_score NUMERIC(5, 2) DEFAULT 0.00,
    severity VARCHAR(20) DEFAULT 'LOW',
    is_flagged BOOLEAN DEFAULT FALSE,
    review_status VARCHAR(50) DEFAULT 'AI_FLAGGED',
    review_remarks TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE milestones (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    planned_start_date DATE NOT NULL,
    planned_end_date DATE NOT NULL,
    actual_start_date DATE,
    actual_end_date DATE,
    completion_percentage DOUBLE PRECISION DEFAULT 0.0,
    status VARCHAR(50) DEFAULT 'Pending'
);

CREATE TABLE evidence (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    image_path VARCHAR(500) NOT NULL,
    image_hash VARCHAR(64) NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    uploaded_by VARCHAR(100) DEFAULT 'Field Inspector',
    description TEXT,
    is_duplicate_flag BOOLEAN DEFAULT FALSE
);

CREATE TABLE fund_disbursements (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    disbursement_date DATE NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    tranche_number INTEGER NOT NULL,
    remarks TEXT
);

CREATE TABLE anomaly_logs (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    anomaly_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    confidence_score NUMERIC(5, 2) NOT NULL,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    details TEXT NOT NULL,
    llm_explanation TEXT
);

CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    user_id INTEGER,
    username VARCHAR(100) DEFAULT 'System',
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL DEFAULT 'Project',
    entity_id INTEGER NOT NULL,
    old_value TEXT,
    new_value TEXT,
    remarks TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    previous_hash VARCHAR(64) NOT NULL DEFAULT '0000000000000000000000000000000000000000000000000000000000000000',
    record_hash VARCHAR(64) NOT NULL
);

CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'LOW',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_projects_mp ON projects(mp_id);
CREATE INDEX idx_projects_district ON projects(district_id);
CREATE INDEX idx_projects_contractor ON projects(contractor_id);
CREATE INDEX idx_projects_flagged ON projects(is_flagged);
CREATE INDEX idx_projects_category ON projects(category);
CREATE INDEX idx_projects_severity ON projects(severity);
CREATE INDEX idx_projects_review_status ON projects(review_status);
CREATE INDEX idx_projects_geo_flag ON projects(geo_anomaly_flag);
CREATE INDEX idx_anomaly_severity ON anomaly_logs(severity);
CREATE INDEX idx_evidence_hash ON evidence(image_hash);
CREATE INDEX idx_notifications_read ON notifications(is_read);
