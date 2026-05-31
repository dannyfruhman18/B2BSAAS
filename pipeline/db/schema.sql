-- Brightwick pipeline database schema
-- SQLite. Run once: sqlite3 brightwick.db < schema.sql

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ---------------------------------------------------------------
-- Companies (leads) — one row per UK Ltd/LLP scraped
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS companies (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    company_number      TEXT    UNIQUE NOT NULL,   -- CH number e.g. "12345678"
    company_name        TEXT    NOT NULL,
    company_type        TEXT    NOT NULL,           -- "ltd" | "llp" | "scottish-partnership" etc.
    company_status      TEXT    NOT NULL,           -- must be "active"
    sic_code            TEXT,                       -- primary SIC code
    sic_description     TEXT,
    incorporated_date   TEXT,                       -- ISO 8601
    registered_address  TEXT,                       -- full JSON from CH
    region              TEXT,                       -- our search region label
    officer_names       TEXT,                       -- JSON array of director names
    discovered_domain   TEXT,                       -- best guess domain or NULL
    domain_confirmed    INTEGER DEFAULT 0,          -- 1 = HEAD request returned 200
    scraped_at          TEXT    DEFAULT (datetime('now')),
    -- lifecycle
    status              TEXT    DEFAULT 'new',      -- new|qualified|personalised|outreach|hot|won|dead|opted_out
    opted_out_at        TEXT
);

-- ---------------------------------------------------------------
-- Qualification scores
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS qualifications (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id          INTEGER NOT NULL REFERENCES companies(id),
    score               INTEGER NOT NULL,           -- 0-100; higher = weaker online presence
    no_website          INTEGER DEFAULT 0,
    no_ssl              INTEGER DEFAULT 0,
    lighthouse_mobile   INTEGER,                    -- raw score (NULL if no site)
    last_modified_days  INTEGER,                    -- days since Last-Modified header
    no_social           INTEGER DEFAULT 0,
    low_reviews         INTEGER DEFAULT 0,
    weakness_summary    TEXT,                       -- one-line for LLM personalisation
    qualified_at        TEXT    DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------
-- Generated email copy
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS emails (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id          INTEGER NOT NULL REFERENCES companies(id),
    variant             INTEGER NOT NULL DEFAULT 0, -- 0=initial, 1=followup1, 2=followup2
    subject             TEXT    NOT NULL,
    body_text           TEXT    NOT NULL,
    llm_used            TEXT,                       -- "gemini" | "groq"
    generated_at        TEXT    DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------
-- Outreach log — one row per send attempt
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS outreach (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id          INTEGER NOT NULL REFERENCES companies(id),
    email_id            INTEGER REFERENCES emails(id),
    sent_to             TEXT    NOT NULL,           -- email address sent to
    variant             INTEGER NOT NULL DEFAULT 0,
    scheduled_for       TEXT,                       -- ISO 8601 datetime
    sent_at             TEXT,
    status              TEXT    DEFAULT 'queued',   -- queued|sent|bounced|replied|opted_out
    smtp_message_id     TEXT,
    error               TEXT
);

-- ---------------------------------------------------------------
-- Reply detection
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS replies (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id          INTEGER REFERENCES companies(id),
    outreach_id         INTEGER REFERENCES outreach(id),
    from_email          TEXT,
    subject             TEXT,
    snippet             TEXT,                       -- first 200 chars
    is_opt_out          INTEGER DEFAULT 0,
    detected_at         TEXT    DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------
-- Clients (converted leads)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clients (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id          INTEGER REFERENCES companies(id),
    client_name         TEXT    NOT NULL,
    contact_name        TEXT,
    contact_email       TEXT,
    monthly_value_gbp   REAL,
    won_at              TEXT    DEFAULT (datetime('now')),
    notes               TEXT,
    -- fulfilment status flags
    website_deployed    INTEGER DEFAULT 0,
    ads_delivered       INTEGER DEFAULT 0,
    seo_delivered       INTEGER DEFAULT 0,
    social_delivered    INTEGER DEFAULT 0,
    onboarding_started  INTEGER DEFAULT 0,
    site_url            TEXT
);

-- ---------------------------------------------------------------
-- Pipeline events log (audit trail)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id  INTEGER REFERENCES companies(id),
    event_type  TEXT NOT NULL,                      -- scrape|qualify|personalise|send|reply|won|dead
    detail      TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_companies_status  ON companies(status);
CREATE INDEX IF NOT EXISTS idx_companies_region  ON companies(region);
CREATE INDEX IF NOT EXISTS idx_outreach_status   ON outreach(status);
CREATE INDEX IF NOT EXISTS idx_outreach_scheduled ON outreach(scheduled_for);
CREATE INDEX IF NOT EXISTS idx_events_company    ON events(company_id);
