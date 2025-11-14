-- Audit logs table for tracking status changes and RAG toggles (Section 11)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    capsule_id TEXT NOT NULL,
    action_type TEXT NOT NULL, -- 'status_change' or 'rag_toggle'
    old_value TEXT,
    new_value TEXT,
    actor TEXT DEFAULT 'system', -- User ID or 'system'
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata JSONB -- Additional context
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_capsule_id ON audit_logs(capsule_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action_type ON audit_logs(action_type);

COMMENT ON TABLE audit_logs IS 'Audit trail for capsule status changes and RAG toggle operations (Section 11: Security & Privacy Defaults)';
