-- CapsuleStore schema aligned with N1Hub v0.1 capsule spec
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS capsules (
    id TEXT PRIMARY KEY,
    version TEXT NOT NULL,
    status TEXT NOT NULL,
    author TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    language TEXT NOT NULL,
    semantic_hash TEXT NOT NULL,
    include_in_rag BOOLEAN NOT NULL DEFAULT true,
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS capsule_vectors (
    capsule_id TEXT REFERENCES capsules(id) ON DELETE CASCADE,
    embedding vector(1536) NOT NULL,
    method TEXT NOT NULL DEFAULT 'hnsw',
    inserted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (capsule_id)
);

CREATE TABLE IF NOT EXISTS links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    src TEXT REFERENCES capsules(id) ON DELETE CASCADE,
    rel TEXT NOT NULL,
    dst TEXT REFERENCES capsules(id) ON DELETE CASCADE,
    confidence REAL NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    code INTEGER NOT NULL DEFAULT 100,
    stage TEXT NOT NULL DEFAULT 'queued',
    state TEXT NOT NULL,
    progress INTEGER NOT NULL DEFAULT 0,
    error JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS artifacts (
    job_id TEXT REFERENCES jobs(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    uri TEXT NOT NULL,
    expires_at TIMESTAMPTZ,
    PRIMARY KEY (job_id, uri)
);

CREATE TABLE IF NOT EXISTS query_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query TEXT NOT NULL,
    scope TEXT[],
    retrieved_capsule_ids TEXT[] NOT NULL,
    scores JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_query_logs_created_at ON query_logs(created_at);

COMMENT ON TABLE capsules IS 'Capsule contract: metadata + payload jsonb. Semantic hash mirrored with neuro_concentrate.';
COMMENT ON TABLE capsule_vectors IS 'pgvector store for retrieval pipeline (chunk_size=800, stride=200).';
COMMENT ON TABLE links IS 'Graph hop=1 edges that power /graph view and router health checks.';
COMMENT ON TABLE jobs IS 'DeepMine 9-step jobs (INGEST>REPORT).';
COMMENT ON TABLE artifacts IS 'References to stored outputs (chunks, exports).';
COMMENT ON TABLE query_logs IS 'Chat query logs for observability: retrieval metrics, faithfulness, citation share.';
