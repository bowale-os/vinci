-- =============================================================================
-- Vinci: Full Snowflake Schema
-- Run this once in your Snowflake worksheet against vinci_db
-- =============================================================================

USE DATABASE vinci_db;
USE SCHEMA insurer_policies;

-- 1. Local Coverage Determinations -----------------------------------------
CREATE TABLE IF NOT EXISTS lcds (
    lcd_id              VARCHAR(50)   PRIMARY KEY,
    title               VARCHAR(500),
    contractor          VARCHAR(200),
    mac_jurisdiction    VARCHAR(10),
    states              ARRAY,
    effective_date      DATE,
    retirement_date     DATE,
    status              VARCHAR(20),
    indications_text    TEXT,
    covered_icd10s      ARRAY,
    covered_cpts        ARRAY,
    noncovered_text     TEXT,
    source_url          VARCHAR(1000),
    last_updated        TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 2. National Coverage Determinations --------------------------------------
CREATE TABLE IF NOT EXISTS ncds (
    ncd_id              VARCHAR(50)   PRIMARY KEY,
    title               VARCHAR(500),
    manual_section      VARCHAR(50),
    effective_date      DATE,
    coverage_summary    TEXT,
    covered_indications ARRAY,
    noncovered_indications ARRAY,
    source_url          VARCHAR(1000),
    last_updated        TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 3. NCCI CCI Edits (procedure-to-procedure) --------------------------------
CREATE TABLE IF NOT EXISTS cci_edits (
    id                  NUMBER AUTOINCREMENT PRIMARY KEY,
    column_one_cpt      VARCHAR(10),
    column_two_cpt      VARCHAR(10),
    modifier_indicator  NUMBER(1),
    effective_date      DATE,
    deletion_date       DATE,
    service_type        VARCHAR(20),
    edit_rationale      VARCHAR(500)
);
CREATE INDEX IF NOT EXISTS idx_cci_col1 ON cci_edits (column_one_cpt);
CREATE INDEX IF NOT EXISTS idx_cci_col2 ON cci_edits (column_two_cpt);

-- 4. NCCI MUE Edits (medically unlikely edits) -----------------------------
CREATE TABLE IF NOT EXISTS mue_edits (
    id                  NUMBER AUTOINCREMENT PRIMARY KEY,
    cpt_code            VARCHAR(10),
    mue_value           NUMBER,
    adjudication_indicator NUMBER(1),
    effective_date      DATE,
    service_type        VARCHAR(20)
);
CREATE INDEX IF NOT EXISTS idx_mue_cpt ON mue_edits (cpt_code);

-- 5. FDA Products (drugs + devices) ----------------------------------------
CREATE TABLE IF NOT EXISTS fda_products (
    product_id          VARCHAR(100)  PRIMARY KEY,
    product_type        VARCHAR(20),
    brand_name          VARCHAR(300),
    generic_name        VARCHAR(300),
    ndc_codes           ARRAY,
    indications_text    TEXT,
    contraindications_text TEXT,
    black_box_warnings  TEXT,
    fda_approval_date   DATE,
    approval_type       VARCHAR(50),
    application_number  VARCHAR(50),
    sponsor_name        VARCHAR(300),
    last_updated        TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 6. Clinical Guidelines ---------------------------------------------------
CREATE TABLE IF NOT EXISTS clinical_guidelines (
    guideline_id        VARCHAR(100)  PRIMARY KEY,
    society             VARCHAR(200),
    guideline_title     VARCHAR(500),
    publication_year    NUMBER(4),
    condition_category  VARCHAR(200),
    cpt_codes           ARRAY,
    icd10_codes         ARRAY,
    recommendation_text TEXT,
    evidence_grade      VARCHAR(10),
    source_url          VARCHAR(1000),
    full_text_chunk     TEXT,
    embedded_at         TIMESTAMP_NTZ
);

-- 7. State Regulations -----------------------------------------------------
CREATE TABLE IF NOT EXISTS state_regulations (
    state_code                      CHAR(2)  PRIMARY KEY,
    state_name                      VARCHAR(100),
    internal_appeal_deadline_days   NUMBER,
    external_review_deadline_days   NUMBER,
    iro_name                        VARCHAR(300),
    iro_phone                       VARCHAR(30),
    iro_website                     VARCHAR(500),
    step_therapy_override_law       BOOLEAN DEFAULT FALSE,
    step_therapy_statute            VARCHAR(500),
    ai_denial_prohibition           BOOLEAN DEFAULT FALSE,
    ai_prohibition_statute          VARCHAR(500),
    expedited_appeal_hours          NUMBER,
    last_verified                   DATE
);

-- 8. PubMed Cache ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS pubmed_cache (
    id              NUMBER AUTOINCREMENT PRIMARY KEY,
    query_key       VARCHAR(500),
    cpt_code        VARCHAR(10),
    condition_term  VARCHAR(300),
    pmid            VARCHAR(20),
    title           VARCHAR(1000),
    authors         ARRAY,
    journal         VARCHAR(300),
    publication_year NUMBER(4),
    abstract_text   TEXT,
    citation_count  NUMBER,
    evidence_type   VARCHAR(50),
    cached_at       TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
CREATE INDEX IF NOT EXISTS idx_pubmed_qkey ON pubmed_cache (query_key);
CREATE INDEX IF NOT EXISTS idx_pubmed_cpt  ON pubmed_cache (cpt_code);

-- 9. Denial Precedents -----------------------------------------------------
CREATE TABLE IF NOT EXISTS denial_precedents (
    precedent_id                VARCHAR(100) PRIMARY KEY,
    insurer                     VARCHAR(200),
    denial_reason_category      VARCHAR(200),
    cpb_number                  VARCHAR(50),
    cpt_code                    VARCHAR(10),
    icd10_code                  VARCHAR(20),
    successful_rebuttal_strategy TEXT,
    evidence_types_used         ARRAY,
    appeal_outcome              VARCHAR(50),
    created_at                  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 10. Clinical Policy Bulletins (CPBs) — private insurer coverage policies ----
CREATE TABLE IF NOT EXISTS cpbs (
    cpb_number      VARCHAR(20),
    insurer_name    VARCHAR(100),
    procedure_code  VARCHAR(20),
    policy_title    VARCHAR(500),
    criteria        TEXT,
    last_reviewed   DATE,
    PRIMARY KEY (cpb_number, insurer_name)
);
