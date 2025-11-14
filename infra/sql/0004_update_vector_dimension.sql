-- Migration 0004: Update vector dimension from 1536 to 384 for all-MiniLM-L6-v2 embeddings
-- This migration updates the capsule_vectors table to use 384-dimensional vectors
-- which matches the output dimension of the all-MiniLM-L6-v2 sentence-transformers model.
--
-- NOTE: This migration will drop existing embeddings. Since we're migrating from
-- placeholder (non-semantic) embeddings to real semantic embeddings, all embeddings
-- should be regenerated via the pipeline anyway.

-- Drop the existing embedding column (idempotent with IF EXISTS)
ALTER TABLE capsule_vectors DROP COLUMN IF EXISTS embedding;

-- Recreate the embedding column with 384 dimensions
ALTER TABLE capsule_vectors ADD COLUMN embedding vector(384) NOT NULL;

-- Add comment
COMMENT ON COLUMN capsule_vectors.embedding IS '384-dimensional semantic embeddings from all-MiniLM-L6-v2 model';
