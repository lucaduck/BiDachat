BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE users (
    id uuid PRIMARY KEY,
    email text NOT NULL,
    password_hash text NOT NULL,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT users_email_normalized_check
        CHECK (email = lower(btrim(email)) AND length(email) > 0),
    CONSTRAINT users_password_hash_not_empty_check
        CHECK (length(btrim(password_hash)) > 0)
);

CREATE UNIQUE INDEX users_email_unique_idx ON users (lower(email));

CREATE TABLE auth_sessions (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    token_hash text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    revoked_at timestamptz,
    CONSTRAINT auth_sessions_token_hash_not_empty_check
        CHECK (length(btrim(token_hash)) > 0),
    CONSTRAINT auth_sessions_expiration_check
        CHECK (expires_at > created_at),
    CONSTRAINT auth_sessions_revocation_check
        CHECK (revoked_at IS NULL OR revoked_at >= created_at)
);

CREATE INDEX auth_sessions_user_id_idx ON auth_sessions (user_id);
CREATE INDEX auth_sessions_expires_at_idx ON auth_sessions (expires_at);

CREATE TABLE llm_models (
    id uuid PRIMARY KEY,
    provider text NOT NULL,
    model text NOT NULL,
    CONSTRAINT llm_models_provider_normalized_check
        CHECK (provider = lower(btrim(provider)) AND length(provider) > 0),
    CONSTRAINT llm_models_model_not_empty_check
        CHECK (model = btrim(model) AND length(model) > 0),
    CONSTRAINT llm_models_provider_model_unique UNIQUE (provider, model)
);

CREATE FUNCTION prevent_llm_model_identity_update()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.provider IS DISTINCT FROM OLD.provider
        OR NEW.model IS DISTINCT FROM OLD.model THEN
        RAISE EXCEPTION 'Provider/model combinations are immutable; create a new row'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END
$$;

CREATE TRIGGER llm_models_identity_update_guard
BEFORE UPDATE OF provider, model ON llm_models
FOR EACH ROW EXECUTE FUNCTION prevent_llm_model_identity_update();

CREATE TABLE chatbots (
    id uuid PRIMARY KEY,
    created_by uuid NOT NULL REFERENCES users (id) ON DELETE RESTRICT,
    configured_llm_model_id uuid NOT NULL REFERENCES llm_models (id) ON DELETE RESTRICT,
    name text NOT NULL,
    description text,
    behavior_instructions text NOT NULL DEFAULT '',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chatbots_name_not_empty_check
        CHECK (length(btrim(name)) > 0)
);

CREATE INDEX chatbots_created_by_idx ON chatbots (created_by);
CREATE INDEX chatbots_configured_llm_model_id_idx
    ON chatbots (configured_llm_model_id);

CREATE TABLE documents (
    id uuid PRIMARY KEY,
    chatbot_id uuid NOT NULL REFERENCES chatbots (id) ON DELETE CASCADE,
    original_filename text NOT NULL,
    storage_key text NOT NULL UNIQUE,
    media_type text NOT NULL,
    size_bytes bigint NOT NULL,
    status text NOT NULL DEFAULT 'pending',
    error_code text,
    embedding_model text,
    embedding_dimensions integer,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    processed_at timestamptz,
    CONSTRAINT documents_filename_not_empty_check
        CHECK (length(btrim(original_filename)) > 0),
    CONSTRAINT documents_storage_key_not_empty_check
        CHECK (length(btrim(storage_key)) > 0),
    CONSTRAINT documents_media_type_not_empty_check
        CHECK (length(btrim(media_type)) > 0),
    CONSTRAINT documents_size_check CHECK (size_bytes > 0),
    CONSTRAINT documents_status_check
        CHECK (status IN ('pending', 'processing', 'ready', 'failed')),
    CONSTRAINT documents_embedding_profile_pair_check
        CHECK ((embedding_model IS NULL) = (embedding_dimensions IS NULL)),
    CONSTRAINT documents_embedding_model_not_empty_check
        CHECK (embedding_model IS NULL OR length(btrim(embedding_model)) > 0),
    CONSTRAINT documents_embedding_dimensions_check
        CHECK (embedding_dimensions IS NULL OR embedding_dimensions = :embedding_dimensions),
    CONSTRAINT documents_processed_at_check
        CHECK (processed_at IS NULL OR processed_at >= created_at),
    CONSTRAINT documents_state_check CHECK (
        (
            status = 'pending'
            AND embedding_model IS NULL
            AND processed_at IS NULL
            AND error_code IS NULL
        )
        OR (
            status = 'processing'
            AND embedding_model IS NOT NULL
            AND processed_at IS NULL
            AND error_code IS NULL
        )
        OR (
            status = 'ready'
            AND embedding_model IS NOT NULL
            AND processed_at IS NOT NULL
            AND error_code IS NULL
        )
        OR (
            status = 'failed'
            AND error_code IS NOT NULL
            AND length(btrim(error_code)) > 0
            AND processed_at IS NULL
        )
    )
);

CREATE INDEX documents_chatbot_id_status_idx ON documents (chatbot_id, status);

CREATE TABLE document_chunks (
    id uuid PRIMARY KEY,
    document_id uuid NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    chunk_index integer NOT NULL,
    content text NOT NULL,
    page_number integer,
    embedding vector(:embedding_dimensions) NOT NULL,
    CONSTRAINT document_chunks_document_index_unique
        UNIQUE (document_id, chunk_index),
    CONSTRAINT document_chunks_index_check CHECK (chunk_index >= 0),
    CONSTRAINT document_chunks_content_not_empty_check
        CHECK (length(btrim(content)) > 0),
    CONSTRAINT document_chunks_page_number_check
        CHECK (page_number IS NULL OR page_number > 0),
    CONSTRAINT document_chunks_embedding_norm_check
        CHECK (vector_norm(embedding) > 0)
);

CREATE TABLE queries (
    id uuid PRIMARY KEY,
    chatbot_id uuid NOT NULL REFERENCES chatbots (id) ON DELETE CASCADE,
    executed_llm_model_id uuid NOT NULL REFERENCES llm_models (id) ON DELETE RESTRICT,
    question text NOT NULL,
    answer text,
    has_image boolean NOT NULL DEFAULT false,
    status text NOT NULL DEFAULT 'processing',
    error_code text,
    received_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    response_time_ms bigint,
    CONSTRAINT queries_question_not_empty_check
        CHECK (length(btrim(question)) > 0),
    CONSTRAINT queries_status_check
        CHECK (status IN ('processing', 'completed', 'failed')),
    CONSTRAINT queries_completed_at_check
        CHECK (completed_at IS NULL OR completed_at >= received_at),
    CONSTRAINT queries_response_time_check
        CHECK (response_time_ms IS NULL OR response_time_ms >= 0),
    CONSTRAINT queries_state_check CHECK (
        (
            status = 'processing'
            AND answer IS NULL
            AND error_code IS NULL
            AND completed_at IS NULL
            AND response_time_ms IS NULL
        )
        OR (
            status = 'completed'
            AND answer IS NOT NULL
            AND length(btrim(answer)) > 0
            AND error_code IS NULL
            AND completed_at IS NOT NULL
            AND response_time_ms IS NOT NULL
        )
        OR (
            status = 'failed'
            AND answer IS NULL
            AND error_code IS NOT NULL
            AND length(btrim(error_code)) > 0
            AND (
                (completed_at IS NULL AND response_time_ms IS NULL)
                OR (completed_at IS NOT NULL AND response_time_ms IS NOT NULL)
            )
        )
    )
);

CREATE INDEX queries_chatbot_id_received_at_idx
    ON queries (chatbot_id, received_at);
CREATE INDEX queries_executed_llm_model_id_idx
    ON queries (executed_llm_model_id);

COMMIT;
