BEGIN;

CREATE TABLE conversations (
    id uuid PRIMARY KEY,
    chatbot_id uuid NOT NULL REFERENCES chatbots (id) ON DELETE CASCADE,
    origin text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    last_active_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    CONSTRAINT conversations_origin_not_empty_check
        CHECK (length(btrim(origin)) > 0),
    CONSTRAINT conversations_expiration_check
        CHECK (expires_at > created_at),
    CONSTRAINT conversations_last_active_check
        CHECK (last_active_at >= created_at)
);

CREATE INDEX conversations_chatbot_origin_expires_idx
    ON conversations (chatbot_id, origin, expires_at);
CREATE INDEX conversations_expires_at_idx ON conversations (expires_at);

ALTER TABLE queries
    ADD COLUMN conversation_id uuid
    REFERENCES conversations (id) ON DELETE SET NULL;

CREATE INDEX queries_conversation_received_at_idx
    ON queries (conversation_id, received_at)
    WHERE conversation_id IS NOT NULL;

CREATE TABLE conversation_messages (
    id uuid PRIMARY KEY,
    conversation_id uuid NOT NULL REFERENCES conversations (id) ON DELETE CASCADE,
    query_id uuid REFERENCES queries (id) ON DELETE SET NULL,
    role text NOT NULL,
    content text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT conversation_messages_role_check
        CHECK (role IN ('user', 'assistant')),
    CONSTRAINT conversation_messages_content_not_empty_check
        CHECK (length(btrim(content)) > 0)
);

CREATE INDEX conversation_messages_conversation_created_idx
    ON conversation_messages (conversation_id, created_at, id);
CREATE INDEX conversation_messages_query_id_idx
    ON conversation_messages (query_id)
    WHERE query_id IS NOT NULL;

COMMIT;
