#!/bin/sh
set -eu

# Run from the production checkout. Keep backup files outside the checkout.
if [ ! -f docker-compose.production.yml ] || [ ! -f .env ]; then
    printf 'Run this script from the production checkout with .env present.\n' >&2
    exit 1
fi

: "${BACKUP_DIR:?Set BACKUP_DIR to an absolute directory outside the checkout}"
retention_days=${BACKUP_RETENTION_DAYS:-7}
case "$retention_days" in
    ''|*[!0-9]*) printf 'BACKUP_RETENTION_DAYS must be a positive integer.\n' >&2; exit 1 ;;
esac
if [ "$retention_days" -lt 1 ]; then
    printf 'BACKUP_RETENTION_DAYS must be at least 1.\n' >&2
    exit 1
fi
case "$BACKUP_DIR" in
    /*) ;;
    *) printf 'BACKUP_DIR must be absolute.\n' >&2; exit 1 ;;
esac

umask 077
mkdir -p "$BACKUP_DIR"
backup_root=$(cd "$BACKUP_DIR" && pwd -P)
checkout_root=$(pwd -P)
case "$backup_root" in
    /|"$checkout_root"|"$checkout_root"/*)
        printf 'BACKUP_DIR must be outside the checkout.\n' >&2
        exit 1
        ;;
esac

acceleration=$(sed -n 's/^OLLAMA_ACCELERATION=//p' .env | head -n 1 | tr -d '\r')
case "${acceleration:-cpu}" in
    cpu|gpu) ;;
    *) printf 'OLLAMA_ACCELERATION must be cpu or gpu.\n' >&2; exit 1 ;;
esac

if [ "${acceleration:-cpu}" = gpu ]; then
    compose() { docker compose -f docker-compose.production.yml -f docker-compose.gpu.yml "$@"; }
else
    compose() { docker compose -f docker-compose.production.yml "$@"; }
fi

compose config --quiet
backend_container=$(compose ps -a -q backend)
if [ -z "$backend_container" ]; then
    printf 'Backend container is missing; cannot identify the document volume.\n' >&2
    exit 1
fi
if [ "$(docker inspect -f '{{.State.Running}}' "$backend_container")" != true ]; then
    printf 'Backend must be running before a coordinated backup.\n' >&2
    exit 1
fi

stamp=$(date -u +%Y%m%dT%H%M%SZ)
destination="$backup_root/bidachat-$stamp"
if [ -e "$destination" ]; then
    printf 'Backup destination already exists: %s\n' "$destination" >&2
    exit 1
fi
stage=$(mktemp -d "$backup_root/.partial.XXXXXXXX")
backend_stopped=false
cleanup() {
    result=$?
    trap - EXIT HUP INT TERM
    if [ "$backend_stopped" = true ]; then
        compose start backend || result=1
    fi
    if [ -n "${stage:-}" ] && [ -d "$stage" ]; then
        rm -rf -- "$stage"
    fi
    exit "$result"
}
trap cleanup EXIT HUP INT TERM

# Stop writes before taking both the logical database dump and document copy.
backend_stopped=true
compose stop backend
compose exec -T database sh -c 'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$stage/database.dump"
mkdir "$stage/documents"
docker cp "$backend_container:/app/storage/documents/." "$stage/documents/"
tar -C "$stage/documents" -czf "$stage/documents.tar.gz" .
rm -rf -- "$stage/documents"

compose exec -T database pg_restore --list < "$stage/database.dump" > /dev/null
tar -tzf "$stage/documents.tar.gz" > /dev/null
(cd "$stage" && sha256sum database.dump documents.tar.gz > manifest.sha256)
printf 'created_at_utc=%s\nimage_tag=%s\n' "$stamp" "$(sed -n 's/^IMAGE_TAG=//p' .env | head -n 1 | tr -d '\r')" > "$stage/metadata.txt"

mv -- "$stage" "$destination"
stage=''
compose start backend
backend_stopped=false
printf 'Verified backup: %s\n' "$destination"

# Remove only complete sets after a new verified set exists.
find "$backup_root" -mindepth 1 -maxdepth 1 -type d \
    -name 'bidachat-20??????T??????Z' -mtime "+$retention_days" \
    -exec sh -c 'for directory do
        if [ -f "$directory/manifest.sha256" ]; then
            rm -rf -- "$directory"
        fi
    done' sh {} +
