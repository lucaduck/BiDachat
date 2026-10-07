#!/bin/sh
set -eu

: "${IMAGE_TAG:?Set IMAGE_TAG to the validated commit SHA}"

acceleration=${OLLAMA_ACCELERATION:-}
if [ -z "$acceleration" ] && [ -f .env ]; then
    acceleration=$(awk -F= '$1 == "OLLAMA_ACCELERATION" { gsub(/\r/, "", $2); print $2; exit }' .env)
fi
acceleration=${acceleration:-cpu}

case "$acceleration" in
    cpu)
        ;;
    gpu)
        ;;
    *)
        printf 'OLLAMA_ACCELERATION must be cpu or gpu, received: %s\n' "$acceleration" >&2
        exit 1
        ;;
esac

compose() {
    if [ "$acceleration" = "gpu" ]; then
        docker compose -f docker-compose.production.yml -f docker-compose.gpu.yml "$@"
    else
        docker compose -f docker-compose.production.yml "$@"
    fi
}

printf 'Deploying Ollama with %s acceleration\n' "$acceleration"
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
