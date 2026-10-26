BEGIN;

ALTER TABLE conversations ADD COLUMN identity_hash text;
ALTER TABLE conversations ADD CONSTRAINT conversations_identity_hash_check
    CHECK (identity_hash IS NULL OR identity_hash ~ '^[0-9a-f]{64}$');

COMMIT;
