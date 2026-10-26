BEGIN;

DROP TABLE IF EXISTS conversation_messages;
DROP INDEX IF EXISTS queries_conversation_received_at_idx;
ALTER TABLE queries DROP COLUMN IF EXISTS conversation_id;
DROP TABLE IF EXISTS conversations;

COMMIT;
