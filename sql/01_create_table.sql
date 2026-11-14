-- Drop table if it exists to allow clean resets
DROP TABLE IF EXISTS ap.itsm_incidents;

-- Create the ITSM Incidents table for PTP operations
CREATE TABLE ap.itsm_incidents (
    ticket_id VARCHAR(20) PRIMARY KEY,
    submitted_date TIMESTAMP NOT NULL,
    user_department VARCHAR(50) NOT NULL,
    raw_ticket_text TEXT NOT NULL,
    ai_classified_category VARCHAR(50),
    ai_priority_level VARCHAR(20),
    ai_suggested_action TEXT,
    resolution_status VARCHAR(20) DEFAULT 'Open'
);

-- Create an index on department and status for fast querying
CREATE INDEX idx_itsm_status ON ap.itsm_incidents(resolution_status);