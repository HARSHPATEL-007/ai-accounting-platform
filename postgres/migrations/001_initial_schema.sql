-- AI-Native Accounting Platform - PostgreSQL Schema
-- Compliance: DPDP Act 2023, SOC 2 Type II
-- Features: Row-Level Security, Partitioning, Column Encryption

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- Fuzzy matching for duplicate detection

-- ============================================================
-- 1. CLIENTS & USERS
-- ============================================================

CREATE TYPE client_type AS ENUM ('startup', 'sme', 'corporate', 'foreign_entity');
CREATE TYPE user_role AS ENUM ('admin', 'ca', 'accountant', 'client_user', 'auditor', 'readonly');
CREATE TYPE mfa_type AS ENUM ('totp', 'biometric', 'none');

CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type client_type NOT NULL,
    name VARCHAR(255) NOT NULL,
    pan VARCHAR(10) UNIQUE, -- Format: ABCDE1234F, encrypted at application layer
    gstin VARCHAR(15) UNIQUE, -- Format: 22AAAAA0000A1Z5
    cin VARCHAR(21) UNIQUE, -- Corporate Identification Number
    entity_details JSONB NOT NULL DEFAULT '{}',
    incorporation_date DATE,
    registered_address TEXT,
    billing_address TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ  -- Soft delete for DPDP compliance
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    role user_role NOT NULL DEFAULT 'client_user',
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(15),
    password_hash VARCHAR(255) NOT NULL, -- bcrypt
    mfa_enabled BOOLEAN NOT NULL DEFAULT false,
    mfa_type mfa_type NOT NULL DEFAULT 'none',
    mfa_secret VARCHAR(255), -- encrypted
    last_login_at TIMESTAMPTZ,
    failed_login_attempts INT NOT NULL DEFAULT 0,
    locked_until TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_client_id ON users(client_id);
CREATE INDEX idx_users_email ON users(email);

-- ============================================================
-- 2. LEDGERS (Partitioned by client_id + transaction_date)
-- ============================================================

CREATE TYPE reconciliation_status AS ENUM ('pending', 'matched', 'mismatch', 'flagged', 'approved');
CREATE TYPE transaction_type AS ENUM ('debit', 'credit');

CREATE TABLE ledgers (
    id UUID DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    account_code VARCHAR(50) NOT NULL, -- Chart of accounts code
    transaction_date DATE NOT NULL,
    transaction_type transaction_type NOT NULL,
    amount DECIMAL(18, 2) NOT NULL CHECK (amount >= 0),
    description TEXT,
    gstin VARCHAR(15), -- Vendor GSTIN
    hsn_code VARCHAR(8), -- Harmonized System of Nomenclature
    gst_rate DECIMAL(5, 2), -- e.g., 18.00
    gst_amount DECIMAL(18, 2),
    total_amount DECIMAL(18, 2) GENERATED ALWAYS AS (amount + COALESCE(gst_amount, 0)) STORED,
    reconciliation_status reconciliation_status NOT NULL DEFAULT 'pending',
    bank_transaction_id VARCHAR(255), -- For AA reconciliation
    document_id UUID, -- Reference to documents table
    metadata JSONB DEFAULT '{}',
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    immutable_hash VARCHAR(64), -- SHA-256 of row data for tamper detection
    PRIMARY KEY (id, client_id, transaction_date)
) PARTITION BY RANGE (transaction_date);

-- Create monthly partitions for 2024-2026
CREATE TABLE ledgers_2024_01 PARTITION OF ledgers
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE ledgers_2024_02 PARTITION OF ledgers
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
-- ... (automated partition management in application layer)

CREATE INDEX idx_ledgers_client_date ON ledgers(client_id, transaction_date DESC);
CREATE INDEX idx_ledgers_recon_status ON ledgers(reconciliation_status) WHERE reconciliation_status != 'approved';
CREATE INDEX idx_ledgers_gstin ON ledgers(gstin) WHERE gstin IS NOT NULL;
CREATE INDEX idx_ledgers_trgm_description ON ledgers USING gin(description gin_trgm_ops);

-- ============================================================
-- 3. DOCUMENTS (OCR Pipeline)
-- ============================================================

CREATE TYPE doc_type AS ENUM ('invoice', 'bank_statement', 'receipt', 'contract', 'esg_report', 'tax_notice', 'audit_paper', 'other');
CREATE TYPE ocr_status AS ENUM ('uploaded', 'processing', 'extracted', 'validated', 'failed', 'reviewed');

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    s3_key VARCHAR(512) NOT NULL UNIQUE,
    s3_bucket VARCHAR(255) NOT NULL DEFAULT 'accounting-docs-prod',
    doc_type doc_type NOT NULL DEFAULT 'other',
    file_name VARCHAR(255) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    ocr_status ocr_status NOT NULL DEFAULT 'uploaded',
    ocr_confidence DECIMAL(5, 4), -- 0.0000 to 1.0000
    extraction_json JSONB, -- Structured data from OCR + LLM
    raw_text TEXT, -- Raw OCR text
    classification_confidence DECIMAL(5, 4),
    uploaded_by UUID NOT NULL REFERENCES users(id),
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_documents_client_status ON documents(client_id, ocr_status);
CREATE INDEX idx_documents_type ON documents(doc_type);

-- ============================================================
-- 4. TAX FILINGS
-- ============================================================

CREATE TYPE filing_type AS ENUM ('gstr1', 'gstr3b', 'gstr9', 'itr3', 'itr5', 'itr6', 'tds_return', 'advance_tax');
CREATE TYPE filing_status AS ENUM ('draft', 'filed', 'acknowledged', 'rejected', 'under_review');

CREATE TABLE tax_filings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    filing_type filing_type NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    status filing_status NOT NULL DEFAULT 'draft',
    gstn_acknowledgment VARCHAR(50),
    filing_json JSONB NOT NULL DEFAULT '{}', -- Structured filing data
    filed_by UUID REFERENCES users(id),
    filed_at TIMESTAMPTZ,
    due_date DATE NOT NULL,
    reminder_sent_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tax_filings_client_period ON tax_filings(client_id, period_end DESC);
CREATE INDEX idx_tax_filings_due_date ON tax_filings(due_date) WHERE status != 'acknowledged';

-- ============================================================
-- 5. CMA REPORTS (Credit Monitoring Arrangement)
-- ============================================================

CREATE TABLE cma_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    report_period_start DATE NOT NULL,
    report_period_end DATE NOT NULL,
    financial_data_json JSONB NOT NULL, -- Structured CMA data
    generated_pdf_s3_key VARCHAR(512),
    status VARCHAR(50) NOT NULL DEFAULT 'draft', -- draft, generated, reviewed, approved
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    generated_by UUID NOT NULL REFERENCES users(id),
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMPTZ,
    ai_confidence_score DECIMAL(5, 4),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_cma_client_period ON cma_reports(client_id, report_period_end DESC);

-- ============================================================
-- 6. ESOP GRANTS
-- ============================================================

CREATE TYPE valuation_method AS ENUM ('black_scholes', 'binomial', 'monte_carlo', 'recent_fmv');

CREATE TABLE esop_grants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    employee_id VARCHAR(100) NOT NULL, -- Internal employee reference
    employee_name VARCHAR(255) NOT NULL,
    grant_date DATE NOT NULL,
    number_of_options INT NOT NULL CHECK (number_of_options > 0),
    exercise_price DECIMAL(18, 2) NOT NULL,
    vesting_schedule JSONB NOT NULL, -- [{ cliff_months: 12, vesting_percent: 25 }, ...]
    valuation_method valuation_method NOT NULL,
    fair_market_value DECIMAL(18, 2) NOT NULL, -- 409A valuation
    expiry_date DATE NOT NULL,
    board_approval_date DATE,
    shareholding_dilution DECIMAL(8, 6), -- Percentage
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_esop_client ON esop_grants(client_id);

-- ============================================================
-- 7. AUDIT LOGS (Immutable, Partitioned)
-- ============================================================

CREATE TYPE audit_action AS ENUM ('create', 'read', 'update', 'delete', 'login', 'logout', 'export', 'ai_generate', 'approve', 'reject');
CREATE TYPE resource_type AS ENUM ('client', 'user', 'ledger', 'document', 'tax_filing', 'cma_report', 'esop_grant', 'rag_document');

CREATE TABLE audit_logs (
    id UUID DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action audit_action NOT NULL,
    resource_type resource_type NOT NULL,
    resource_id UUID,
    ip_address INET NOT NULL,
    user_agent TEXT,
    request_id VARCHAR(100) NOT NULL, -- Correlation ID
    details JSONB NOT NULL DEFAULT '{}', -- Before/after values for updates
    immutable_hash VARCHAR(64) NOT NULL, -- SHA-256 chain: hash(prev_hash + current_row)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

CREATE TABLE audit_logs_2024_01 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
-- Automated partition creation via cron/job

CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_request ON audit_logs(request_id);

-- ============================================================
-- 8. RAG DOCUMENTS (Knowledge Base)
-- ============================================================

CREATE TYPE rag_doc_type AS ENUM ('tax_act', 'gst_circular', 'fema_regulation', 'mca_rule', 'dtaa_treaty', 'court_judgment', 'internal_template');
CREATE TYPE jurisdiction_type AS ENUM ('central', 'state_maharashtra', 'state_karnataka', 'state_delhi', 'state_tamil_nadu', 'international');

CREATE TABLE rag_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_url VARCHAR(512) NOT NULL,
    doc_type rag_doc_type NOT NULL,
    jurisdiction jurisdiction_type NOT NULL DEFAULT 'central',
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    chunk_index INT NOT NULL DEFAULT 0,
    chunk_size INT NOT NULL,
    embedding_id VARCHAR(255), -- Reference to vector DB (Pinecone/Milvus)
    metadata JSONB DEFAULT '{}', -- { section: '115BAC', act_year: 2023, amendment_date: ... }
    effective_date DATE,
    is_current BOOLEAN NOT NULL DEFAULT true, -- Superseded by newer version?
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rag_doc_type ON rag_documents(doc_type);
CREATE INDEX idx_rag_jurisdiction ON rag_documents(jurisdiction);
CREATE INDEX idx_rag_current ON rag_documents(is_current) WHERE is_current = true;
CREATE INDEX idx_rag_metadata ON rag_documents USING gin(metadata);

-- ============================================================
-- 9. WORKFLOW EXECUTIONS (Temporal/Custom)
-- ============================================================

CREATE TYPE workflow_status AS ENUM ('running', 'completed', 'failed', 'cancelled', 'compensating');

CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_type VARCHAR(100) NOT NULL, -- 'invoice_to_ledger', 'cma_generation', 'tax_filing'
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    status workflow_status NOT NULL DEFAULT 'running',
    input_json JSONB NOT NULL,
    result_json JSONB,
    error_message TEXT,
    run_id VARCHAR(255) NOT NULL UNIQUE, -- Temporal run ID or internal UUID
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    created_by UUID NOT NULL REFERENCES users(id)
);

CREATE INDEX idx_workflow_client ON workflow_executions(client_id, started_at DESC);
CREATE INDEX idx_workflow_status ON workflow_executions(status) WHERE status = 'running';

-- ============================================================
-- 10. ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================

ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE ledgers ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_filings ENABLE ROW LEVEL SECURITY;
ALTER TABLE cma_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE esop_grants ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_executions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own client's data
CREATE POLICY client_isolation_policy ON clients
    FOR ALL TO app_user
    USING (id IN (SELECT client_id FROM users WHERE id = current_setting('app.current_user_id')::UUID));

CREATE POLICY user_isolation_policy ON users
    FOR ALL TO app_user
    USING (client_id IN (SELECT client_id FROM users WHERE id = current_setting('app.current_user_id')::UUID));

CREATE POLICY ledger_isolation_policy ON ledgers
    FOR ALL TO app_user
    USING (client_id IN (SELECT client_id FROM users WHERE id = current_setting('app.current_user_id')::UUID));

CREATE POLICY document_isolation_policy ON documents
    FOR ALL TO app_user
    USING (client_id IN (SELECT client_id FROM users WHERE id = current_setting('app.current_user_id')::UUID));

-- ============================================================
-- 11. FUNCTIONS & TRIGGERS
-- ============================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_ledgers_updated_at BEFORE UPDATE ON ledgers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_tax_filings_updated_at BEFORE UPDATE ON tax_filings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_esop_grants_updated_at BEFORE UPDATE ON esop_grants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Immutable hash generation for ledgers (tamper detection)
CREATE OR REPLACE FUNCTION generate_ledger_hash()
RETURNS TRIGGER AS $$
BEGIN
    NEW.immutable_hash = encode(digest(
        NEW.id::text || NEW.client_id::text || NEW.account_code || NEW.transaction_date::text || 
        NEW.amount::text || NEW.description || COALESCE(NEW.gstin, '') || NEW.created_at::text,
        'sha256'
    ), 'hex');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_ledger_hash BEFORE INSERT OR UPDATE ON ledgers
    FOR EACH ROW EXECUTE FUNCTION generate_ledger_hash();

-- ============================================================
-- 12. SEED DATA
-- ============================================================

INSERT INTO clients (id, type, name, pan, gstin, cin, entity_details, incorporation_date)
VALUES 
    ('11111111-1111-1111-1111-111111111111', 'startup', 'TechStart Pvt Ltd', 'AAACS1234A', '22AAAAA0000A1Z5', 'U72200MH2024PTC123456', '{"sector": "technology", "funding_stage": "seed"}', '2024-01-15'),
    ('22222222-2222-2222-2222-222222222222', 'sme', 'MSME Manufacturing', 'AABCM5678B', '27BBBBB1111B1Z3', 'U28910PN2023PTC789012', '{"sector": "manufacturing", "employees": 50}', '2023-06-01'),
    ('33333333-3333-3333-3333-333333333333', 'corporate', 'LargeCorp India Ltd', 'AACCL9012C', '07CCCCC2222C1Z8', 'L17110DL2022PLC345678', '{"sector": "conglomerate", "employees": 5000}', '2022-03-10'),
    ('44444444-4444-4444-4444-444444444444', 'foreign_entity', 'GlobalTech Singapore Pte', NULL, NULL, NULL, '{"parent_country": "singapore", "india_setup_stage": "incorporation"}', NULL);

-- Seed RAG documents (sample)
INSERT INTO rag_documents (source_url, doc_type, jurisdiction, title, content, chunk_index, chunk_size, metadata, effective_date)
VALUES 
    ('https://www.incometaxindia.gov.in/_layouts/15/dit/Pages/viewer.aspx?path=/act&name=Section 115BAC', 'tax_act', 'central', 'Income Tax Act - Section 115BAC', 
     '115BAC. (1) Notwithstanding anything contained in this Act but subject to the provisions of this Chapter, an individual or Hindu undivided family or association of persons or body of individuals...',
     0, 500, '{"section": "115BAC", "act_year": 2023, "topic": "new_tax_regime"}', '2023-04-01');
