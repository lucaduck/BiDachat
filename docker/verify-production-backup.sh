#!/bin/sh
set -eu

if [ "$#" -ne 1 ] || [ ! -d "$1" ]; then
    printf 'Usage: %s /absolute/path/to/bidachat-backup\n' "$0" >&2
    exit 1
fi

bundle=$(cd "$1" && pwd -P)
if [ ! -f "$bundle/database.dump" ] || [ ! -f "$bundle/documents.tar.gz" ] || [ ! -f "$bundle/manifest.sha256" ]; then
    printf 'Backup set is incomplete.\n' >&2
    exit 1
fi
(cd "$bundle" && sha256sum --check --status manifest.sha256)
tar -tzf "$bundle/documents.tar.gz" > /dev/null

if [ ! -f docker-compose.production.yml ] || [ ! -f .env ]; then
    printf 'Run from the production checkout to use its PostgreSQL image.\n' >&2
    exit 1
fi

database_container=$(docker compose -f docker-compose.production.yml ps -a -q database)
if [ -z "$database_container" ]; then
    printf 'Production database container is unavailable.\n' >&2
    exit 1
fi
image=$(docker inspect -f '{{.Config.Image}}' "$database_container")
unique="$$-$(date -u +%s)"
container="bidachat-restore-$unique"
volume="bidachat_restore_$unique"

cleanup() {
    result=$?
    trap - EXIT HUP INT TERM
    docker rm -f "$container" > /dev/null 2>&1 || true
    docker volume rm "$volume" > /dev/null 2>&1 || true
    exit "$result"
}
trap cleanup EXIT HUP INT TERM

docker volume create "$volume" > /dev/null
docker run -d --name "$container" \
    -e POSTGRES_USER=verify -e POSTGRES_PASSWORD=verify-local-only \
    -e POSTGRES_DB=verify -v "$volume:/var/lib/postgresql/data" \
    "$image" > /dev/null

ready=false
attempt=0
while [ "$attempt" -lt 30 ]; do
    ready_events=$(docker logs "$container" 2>&1 |
        grep -c 'database system is ready to accept connections' || true)
    if [ "$ready_events" -ge 2 ] &&
        docker exec "$container" pg_isready -U verify -d verify > /dev/null 2>&1; then
        ready=true
        break
    fi
    attempt=$((attempt + 1))
    sleep 1
done
if [ "$ready" != true ]; then
    printf 'Isolated PostgreSQL did not become ready.\n' >&2
    exit 1
fi

docker exec -i "$container" pg_restore \
    --exit-on-error --no-owner --no-privileges -U verify -d verify \
    < "$bundle/database.dump"

for table in users chatbots documents document_chunks chatbot_documents queries; do
    docker exec "$container" psql -X -qAt -U verify -d verify \
        -c "SELECT count(*) FROM $table" > /dev/null
done

orphan_associations=$(docker exec "$container" psql -X -qAt -U verify -d verify \
    -c 'SELECT count(*) FROM chatbot_documents cd
        LEFT JOIN chatbots c ON c.id = cd.chatbot_id
        LEFT JOIN documents d ON d.id = cd.document_id
        WHERE c.id IS NULL OR d.id IS NULL')
orphan_chunks=$(docker exec "$container" psql -X -qAt -U verify -d verify \
    -c 'SELECT count(*) FROM document_chunks dc
        LEFT JOIN documents d ON d.id = dc.document_id
        WHERE d.id IS NULL')
unassociated_documents=$(docker exec "$container" psql -X -qAt -U verify -d verify \
    -c 'SELECT count(*) FROM documents d
        LEFT JOIN chatbot_documents cd ON cd.document_id = d.id
        WHERE cd.document_id IS NULL')
if [ "$orphan_associations" -ne 0 ] || [ "$orphan_chunks" -ne 0 ] || \
    [ "$unassociated_documents" -ne 0 ]; then
    printf 'Restored source relationships are inconsistent.\n' >&2
    exit 1
fi

chunk_count=$(docker exec "$container" psql -X -qAt -U verify -d verify \
    -c 'SELECT count(*) FROM document_chunks')
if [ "$chunk_count" -gt 0 ]; then
    recovered_content=$(docker exec "$container" psql -X -qAt -U verify -d verify \
        -c 'WITH target AS (
                SELECT embedding FROM document_chunks ORDER BY id LIMIT 1
            )
            SELECT dc.content
            FROM document_chunks dc
            JOIN chatbot_documents cd ON cd.document_id = dc.document_id
            CROSS JOIN target
            ORDER BY dc.embedding <=> target.embedding
            LIMIT 1')
    if [ -z "$recovered_content" ]; then
        printf 'Restored vectors are not recoverable through chatbot associations.\n' >&2
        exit 1
    fi
fi

docker exec "$container" psql -X -qAt -U verify -d verify \
    -c 'SELECT storage_key FROM documents ORDER BY storage_key' |
while IFS= read -r storage_key; do
    [ -n "$storage_key" ] || continue
    filename=${storage_key##*/}
    if ! tar -tzf "$bundle/documents.tar.gz" | grep -Fx "./$filename" > /dev/null; then
        printf 'Original file missing for a restored document.\n' >&2
        exit 1
    fi
done

printf 'Isolated restore passed: records, source associations, vector recovery and document originals.\n'
