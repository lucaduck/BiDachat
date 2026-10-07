#!/bin/sh
set -eu

: "${IMAGE_TAG:?Set IMAGE_TAG to the validated commit SHA}"

compose() {
    docker compose -f docker-compose.production.yml "$@"
}

compose pull backend frontend nginx
compose up -d --remove-orphans
compose exec -T nginx nginx -t
compose exec -T nginx nginx -s reload

published_port=$(compose port nginx 80)
published_port=${published_port##*:}

attempt=0
while [ "$attempt" -lt 20 ]; do
    if curl --fail --silent --output /dev/null "http://127.0.0.1:${published_port}/api/v1/health"; then
        printf 'BIDACHAT is healthy through Nginx on port %s\n' "$published_port"
        exit 0
    fi
    attempt=$((attempt + 1))
    sleep 2
done

printf 'BIDACHAT did not become healthy through Nginx\n' >&2
exit 1
