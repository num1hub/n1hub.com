-- Validation runs and link suggestions tracking (idempotent)
-- Migration 0002: Add validation_runs and link_suggestions tables

CREATE TABLE IF NOT EXISTS validation_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    capsule_id TEXT REFERENCES capsules(id) ON DELETE CASCADE,
    run_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    strict_mode BOOLEAN NOT NULL DEFAULT false,
    is_valid BOOLEAN NOT NULL,
    error_count INTEGER NOT NULL DEFAULT 0,
    warning_count INTEGER NOT NULL DEFAULT 0,
    auto_fixes_applied TEXT[],
    errors JSONB,
    warnings JSONB
);

CREATE TABLE IF NOT EXISTS link_suggestions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_capsule_id TEXT REFERENCES capsules(id) ON DELETE CASCADE,
    target_capsule_id TEXT REFERENCES capsules(id) ON DELETE CASCADE,
    rel TEXT NOT NULL,
    confidence REAL NOT NULL,
    reason TEXT,
    suggested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    accepted BOOLEAN DEFAULT NULL,
    PRIMARY KEY (source_capsule_id, target_capsule_id, rel)
);

CREATE INDEX IF NOT EXISTS idx_validation_runs_capsule_id ON validation_runs(capsule_id);
CREATE INDEX IF NOT EXISTS idx_validation_runs_run_at ON validation_runs(run_at);
CREATE INDEX IF NOT EXISTS idx_link_suggestions_source ON link_suggestions(source_capsule_id);
CREATE INDEX IF NOT EXISTS idx_link_suggestions_target ON link_suggestions(target_capsule_id);
CREATE INDEX IF NOT EXISTS idx_link_suggestions_accepted ON link_suggestions(accepted) WHERE accepted IS NOT NULL;

COMMENT ON TABLE validation_runs IS 'Track validation runs for capsules with errors, warnings, and auto-fixes applied.';
COMMENT ON TABLE link_suggestions IS 'Track link suggestions from LinkSuggester with acceptance status for audit and learning.';
