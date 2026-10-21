BEGIN;

ALTER TABLE conversations DROP CONSTRAINT IF EXISTS conversations_identity_hash_check;
ALTER TABLE conversations DROP COLUMN IF EXISTS identity_hash;

COMMIT;
