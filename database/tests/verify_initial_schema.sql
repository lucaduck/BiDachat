\set ON_ERROR_STOP on

BEGIN;

SELECT set_config('bidachat.embedding_dimensions', :'embedding_dimensions', true);

DO $$
DECLARE
    missing_tables text[];
BEGIN
    SELECT array_agg(expected_table)
    INTO missing_tables
    FROM unnest(
        ARRAY[
            'users',
            'auth_sessions',
            'llm_models',
            'chatbots',
            'documents',
            'document_chunks',
            'queries'
        ]
    ) AS expected_table
    WHERE to_regclass('public.' || expected_table) IS NULL;

    IF missing_tables IS NOT NULL THEN
        RAISE EXCEPTION 'Missing tables: %', missing_tables;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RAISE EXCEPTION 'The vector extension is not installed';
    END IF;
END
$$;

INSERT INTO users (id, email, password_hash)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'researcher@example.org',
    'test-hash'
);

INSERT INTO auth_sessions (id, user_id, token_hash, expires_at)
VALUES (
    '60000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000001',
    'test-token-hash',
    now() + interval '1 hour'
);

INSERT INTO llm_models (id, provider, model)
VALUES
    ('10000000-0000-0000-0000-000000000001', 'gemini', 'test-gemini'),
    ('10000000-0000-0000-0000-000000000002', 'ollama', 'test-ollama');

INSERT INTO chatbots (
    id,
    created_by,
    configured_llm_model_id,
    name
)
VALUES (
    '20000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000001',
    '10000000-0000-0000-0000-000000000001',
    'Test chatbot'
);

INSERT INTO queries (
    id,
    chatbot_id,
    executed_llm_model_id,
    question,
    answer,
    status,
    completed_at,
    response_time_ms
)
VALUES (
    '30000000-0000-0000-0000-000000000001',
    '20000000-0000-0000-0000-000000000001',
    '10000000-0000-0000-0000-000000000001',
    'Test question',
    'Test answer',
    'completed',
    now(),
    25
);

UPDATE chatbots
SET configured_llm_model_id = '10000000-0000-0000-0000-000000000002'
WHERE id = '20000000-0000-0000-0000-000000000001';

DO $$
DECLARE
    configured_provider text;
    executed_provider text;
BEGIN
    SELECT model.provider
    INTO configured_provider
    FROM chatbots AS chatbot
    JOIN llm_models AS model ON model.id = chatbot.configured_llm_model_id
    WHERE chatbot.id = '20000000-0000-0000-0000-000000000001';

    SELECT model.provider
    INTO executed_provider
    FROM queries AS query_record
    JOIN llm_models AS model ON model.id = query_record.executed_llm_model_id
    WHERE query_record.id = '30000000-0000-0000-0000-000000000001';

    IF configured_provider <> 'ollama' OR executed_provider <> 'gemini' THEN
        RAISE EXCEPTION 'Current configuration and query history were not isolated';
    END IF;
END
$$;

INSERT INTO documents (
    id,
    chatbot_id,
    original_filename,
    storage_key,
    media_type,
    size_bytes,
    status,
    embedding_model,
    embedding_dimensions,
    processed_at
)
VALUES (
    '40000000-0000-0000-0000-000000000001',
    '20000000-0000-0000-0000-000000000001',
    'test.pdf',
    'test/test.pdf',
    'application/pdf',
    100,
    'ready',
    'test-embedding-model',
    :embedding_dimensions,
    now()
);

INSERT INTO document_chunks (
    id,
    document_id,
    chunk_index,
    content,
    page_number,
    embedding
)
VALUES (
    '50000000-0000-0000-0000-000000000001',
    '40000000-0000-0000-0000-000000000001',
    0,
    'Test document content',
    1,
    array_fill(1::real, ARRAY[:embedding_dimensions])::vector
);

DO $$
BEGIN
    BEGIN
        INSERT INTO auth_sessions (id, user_id, token_hash, expires_at)
        VALUES (
            '60000000-0000-0000-0000-000000000002',
            '00000000-0000-0000-0000-000000000001',
            'invalid-session',
            now() - interval '1 hour'
        );
        RAISE EXCEPTION 'A session expiring before creation was accepted';
    EXCEPTION
        WHEN check_violation THEN NULL;
    END;

    BEGIN
        INSERT INTO chatbots (id, created_by, configured_llm_model_id, name)
        VALUES (
            '20000000-0000-0000-0000-000000000002',
            '00000000-0000-0000-0000-000000000001',
            '10000000-0000-0000-0000-000000000099',
            'Invalid model reference'
        );
        RAISE EXCEPTION 'A nonexistent model reference was accepted';
    EXCEPTION
        WHEN foreign_key_violation THEN NULL;
    END;

    BEGIN
        INSERT INTO llm_models (id, provider, model)
        VALUES (
            '10000000-0000-0000-0000-000000000003',
            'gemini',
            'test-gemini'
        );
        RAISE EXCEPTION 'Duplicate provider/model was accepted';
    EXCEPTION
        WHEN unique_violation THEN NULL;
    END;

    BEGIN
        DELETE FROM llm_models
        WHERE id = '10000000-0000-0000-0000-000000000001';
        RAISE EXCEPTION 'A model referenced by query history was deleted';
    EXCEPTION
        WHEN foreign_key_violation THEN NULL;
    END;

    BEGIN
        UPDATE llm_models
        SET provider = 'ollama'
        WHERE id = '10000000-0000-0000-0000-000000000001';
        RAISE EXCEPTION 'A historical provider/model combination was modified';
    EXCEPTION
        WHEN check_violation THEN NULL;
    END;

    BEGIN
        UPDATE queries
        SET answer = NULL
        WHERE id = '30000000-0000-0000-0000-000000000001';
        RAISE EXCEPTION 'A completed query without an answer was accepted';
    EXCEPTION
        WHEN check_violation THEN NULL;
    END;

    BEGIN
        UPDATE documents
        SET status = 'failed', processed_at = NULL, error_code = NULL
        WHERE id = '40000000-0000-0000-0000-000000000001';
        RAISE EXCEPTION 'A failed document without an error code was accepted';
    EXCEPTION
        WHEN check_violation THEN NULL;
    END;

    BEGIN
        INSERT INTO queries (
            id,
            chatbot_id,
            executed_llm_model_id,
            question,
            status,
            response_time_ms
        )
        VALUES (
            '30000000-0000-0000-0000-000000000002',
            '20000000-0000-0000-0000-000000000001',
            '10000000-0000-0000-0000-000000000002',
            'Invalid timing',
            'processing',
            -1
        );
        RAISE EXCEPTION 'An invalid query state was accepted';
    EXCEPTION
        WHEN check_violation THEN NULL;
    END;

    BEGIN
        INSERT INTO document_chunks (
            id, document_id, chunk_index, content, embedding
        )
        VALUES (
            '50000000-0000-0000-0000-000000000002',
            '40000000-0000-0000-0000-000000000001',
            1,
            'Wrong vector dimension',
            array_fill(
                1::real,
                ARRAY[current_setting('bidachat.embedding_dimensions')::integer + 1]
            )::vector
        );
        RAISE EXCEPTION 'A vector with an incompatible dimension was accepted';
    EXCEPTION
        WHEN data_exception THEN NULL;
    END;

    BEGIN
        INSERT INTO document_chunks (
            id, document_id, chunk_index, content, embedding
        )
        SELECT
            '50000000-0000-0000-0000-000000000003',
            document_id,
            chunk_index,
            'Duplicate chunk index',
            embedding
        FROM document_chunks
        WHERE id = '50000000-0000-0000-0000-000000000001';
        RAISE EXCEPTION 'A duplicate document chunk index was accepted';
    EXCEPTION
        WHEN unique_violation THEN NULL;
    END;

    BEGIN
        INSERT INTO document_chunks (
            id, document_id, chunk_index, content, embedding
        )
        VALUES (
            '50000000-0000-0000-0000-000000000004',
            '40000000-0000-0000-0000-000000000001',
            2,
            'Zero vector',
            array_fill(
                0::real,
                ARRAY[current_setting('bidachat.embedding_dimensions')::integer]
            )::vector
        );
        RAISE EXCEPTION 'A zero vector was accepted';
    EXCEPTION
        WHEN check_violation THEN NULL;
    END;
END
$$;

DELETE FROM chatbots
WHERE id = '20000000-0000-0000-0000-000000000001';

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM documents WHERE id = '40000000-0000-0000-0000-000000000001')
        OR EXISTS (SELECT 1 FROM document_chunks WHERE id = '50000000-0000-0000-0000-000000000001')
        OR EXISTS (SELECT 1 FROM queries WHERE id = '30000000-0000-0000-0000-000000000001') THEN
        RAISE EXCEPTION 'Chatbot deletion left dependent data behind';
    END IF;

    IF (SELECT count(*) FROM llm_models WHERE id IN (
        '10000000-0000-0000-0000-000000000001',
        '10000000-0000-0000-0000-000000000002'
    )) <> 2 THEN
        RAISE EXCEPTION 'Chatbot deletion removed model catalog entries';
    END IF;
END
$$;

ROLLBACK;

SELECT 'initial schema verification passed' AS result;
