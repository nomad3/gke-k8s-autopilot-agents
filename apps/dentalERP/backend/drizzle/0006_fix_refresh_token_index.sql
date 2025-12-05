-- Fix refresh_tokens index to use MD5 hash instead of full token
-- This resolves the "index row size exceeds btree maximum" error

-- Drop the existing unique constraint that's causing the problem
ALTER TABLE refresh_tokens
  DROP CONSTRAINT IF EXISTS refresh_tokens_token_key;

-- Add a new column for the token hash
ALTER TABLE refresh_tokens
  ADD COLUMN IF NOT EXISTS token_hash varchar(32);

-- Create an index on the hash column for fast lookups
CREATE INDEX IF NOT EXISTS refresh_tokens_token_hash_idx ON refresh_tokens(token_hash);

-- Add unique constraint on the hash (MD5 collision is astronomically unlikely)
ALTER TABLE refresh_tokens
  ADD CONSTRAINT refresh_tokens_token_hash_key UNIQUE (token_hash);

-- Update metadata
INSERT INTO drizzle.__drizzle_migrations (id, hash, created_at)
VALUES ('0006_fix_refresh_token_index', '0', now())
ON CONFLICT (id) DO NOTHING;
