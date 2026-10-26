#!/bin/sh
set -eu

case "${EMBEDDING_DIMENSIONS:-}" in
    ''|*[!0-9]*)
        printf 'EMBEDDING_DIMENSIONS must be a positive integer.\n' >&2
        exit 1
        ;;
esac
if [ "$EMBEDDING_DIMENSIONS" -le 0 ]; then
    printf 'EMBEDDING_DIMENSIONS must be greater than zero.\n' >&2
    exit 1
fi

psql_base() {
    psql --set ON_ERROR_STOP=1 \
        --username "$POSTGRES_USER" \
        --dbname "$POSTGRES_DB" \
        "$@"
}

query_boolean() {
    psql_base --tuples-only --no-align --command "$1" | tr -d '[:space:]'
}

record_migration() {
    migration=$1
    psql_base --command \
        "INSERT INTO schema_migrations (migration) VALUES ('$migration') ON CONFLICT DO NOTHING;" \
        > /dev/null
}

apply_migration() {
    migration=$1
    file=$2
    printf 'Applying database migration %s\n' "$migration"
    if [ "$migration" = "001_initial_schema" ]; then
        psql_base --set embedding_dimensions="$EMBEDDING_DIMENSIONS" --file "$file"
    else
        psql_base --file "$file"
    fi
    record_migration "$migration"
}

reconcile_migration() {
    migration=$1
    file=$2
    complete_sql=$3
    empty_sql=$4

    if [ "$(query_boolean "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE migration = '$migration');")" = t ]; then
        printf 'Database migration %s already recorded\n' "$migration"
        return
    fi

    if [ "$(query_boolean "$complete_sql")" = t ]; then
        printf 'Recording legacy database migration %s\n' "$migration"
        record_migration "$migration"
        return
    fi

    if [ "$(query_boolean "$empty_sql")" != t ]; then
        printf 'Database migration %s is partially applied; inspect the schema before retrying.\n' "$migration" >&2
        exit 1
    fi

    apply_migration "$migration" "$file"
}

psql_base --command "
    CREATE TABLE IF NOT EXISTS schema_migrations (
        migration text PRIMARY KEY,
        applied_at timestamptz NOT NULL DEFAULT now(),
        CONSTRAINT schema_migrations_name_check
            CHECK (migration ~ '^[0-9]{3}_[a-z0-9_]+$')
    );
" > /dev/null

reconcile_migration \
    001_initial_schema \
    /migrations/001_initial_schema.up.sql \
    "SELECT
        to_regclass('public.users') IS NOT NULL
        AND to_regclass('public.auth_sessions') IS NOT NULL
        AND to_regclass('public.llm_models') IS NOT NULL
        AND to_regclass('public.chatbots') IS NOT NULL
        AND to_regclass('public.documents') IS NOT NULL
        AND to_regclass('public.document_chunks') IS NOT NULL
        AND to_regclass('public.queries') IS NOT NULL
        AND EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector');" \
    "SELECT NOT EXISTS (
        SELECT 1
        FROM unnest(ARRAY[
            'users', 'auth_sessions', 'llm_models', 'chatbots',
            'documents', 'document_chunks', 'queries'
        ]) AS relation_name
        WHERE to_regclass('public.' || relation_name) IS NOT NULL
    );"

reconcile_migration \
    002_login_attempts \
    /migrations/002_login_attempts.up.sql \
    "SELECT to_regclass('public.login_attempts') IS NOT NULL;" \
    "SELECT to_regclass('public.login_attempts') IS NULL;"

reconcile_migration \
    003_widget_settings \
    /migrations/003_widget_settings.up.sql \
    "SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'chatbots'
          AND column_name = 'widget_settings'
    );" \
    "SELECT NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'chatbots'
          AND column_name = 'widget_settings'
    );"

reconcile_migration \
    004_chatbot_document_associations \
    /migrations/004_chatbot_document_associations.up.sql \
    "SELECT
        to_regclass('public.chatbot_documents') IS NOT NULL
        AND to_regclass('public.chatbot_documents_document_id_idx') IS NOT NULL;" \
    "SELECT
        to_regclass('public.chatbot_documents') IS NULL
        AND to_regclass('public.chatbot_documents_document_id_idx') IS NULL;"

reconcile_migration \
    005_conversation_memory \
    /migrations/005_conversation_memory.up.sql \
    "SELECT
        to_regclass('public.conversations') IS NOT NULL
        AND to_regclass('public.conversation_messages') IS NOT NULL
        AND EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'queries'
              AND column_name = 'conversation_id'
        )
        AND to_regclass('public.conversations_chatbot_origin_expires_idx') IS NOT NULL
        AND to_regclass('public.conversations_expires_at_idx') IS NOT NULL
        AND to_regclass('public.queries_conversation_received_at_idx') IS NOT NULL
        AND to_regclass('public.conversation_messages_conversation_created_idx') IS NOT NULL
        AND to_regclass('public.conversation_messages_query_id_idx') IS NOT NULL;" \
    "SELECT
        to_regclass('public.conversations') IS NULL
        AND to_regclass('public.conversation_messages') IS NULL
        AND NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'queries'
              AND column_name = 'conversation_id'
        )
        AND to_regclass('public.conversations_chatbot_origin_expires_idx') IS NULL
        AND to_regclass('public.conversations_expires_at_idx') IS NULL
        AND to_regclass('public.queries_conversation_received_at_idx') IS NULL
        AND to_regclass('public.conversation_messages_conversation_created_idx') IS NULL
        AND to_regclass('public.conversation_messages_query_id_idx') IS NULL;"

reconcile_migration \
    006_conversation_identity \
    /migrations/006_conversation_identity.up.sql \
    "SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'conversations'
          AND column_name = 'identity_hash'
    ) AND EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.conversations'::regclass
          AND conname = 'conversations_identity_hash_check'
    );" \
    "SELECT NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'conversations'
          AND column_name = 'identity_hash'
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.conversations'::regclass
          AND conname = 'conversations_identity_hash_check'
    );"

reconcile_migration \
    007_conversation_feedback \
    /migrations/007_conversation_feedback.up.sql \
    "SELECT
        to_regclass('public.conversation_feedback') IS NOT NULL
        AND to_regclass('public.conversation_feedback_chatbot_offered_idx') IS NOT NULL
        AND to_regclass('public.conversation_feedback_comment_retention_idx') IS NOT NULL;" \
    "SELECT
        to_regclass('public.conversation_feedback') IS NULL
        AND to_regclass('public.conversation_feedback_chatbot_offered_idx') IS NULL
        AND to_regclass('public.conversation_feedback_comment_retention_idx') IS NULL;"

printf 'Database schema is up to date\n'
