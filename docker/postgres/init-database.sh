#!/bin/sh
set -eu

case "${EMBEDDING_DIMENSIONS:-}" in
  ''|*[!0-9]*)
    echo "EMBEDDING_DIMENSIONS must be a positive integer." >&2
    exit 1
    ;;
esac

if [ "$EMBEDDING_DIMENSIONS" -le 0 ]; then
  echo "EMBEDDING_DIMENSIONS must be greater than zero." >&2
  exit 1
fi

psql --set ON_ERROR_STOP=1 \
  --set embedding_dimensions="$EMBEDDING_DIMENSIONS" \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  --file /migrations/001_initial_schema.up.sql

psql --set ON_ERROR_STOP=1 \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  --file /migrations/002_login_attempts.up.sql

psql --set ON_ERROR_STOP=1 \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  --file /migrations/003_widget_settings.up.sql

psql --set ON_ERROR_STOP=1 \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  --file /migrations/004_chatbot_document_associations.up.sql
