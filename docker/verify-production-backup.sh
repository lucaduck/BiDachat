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
    if docker exec "$container" pg_isready -U verify -d verify > /dev/null 2>&1; then
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

printf 'Isolated restore passed: database schema, records and document originals.\n'
