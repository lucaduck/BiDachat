#!/bin/sh
set -eu

: "${IMAGE_TAG:?Set IMAGE_TAG to the validated commit SHA}"

env_value() {
    key=$1
    default=$2
    value=""

    if [ -f .env ]; then
        value=$(awk -F= -v key="$key" '$1 == key { gsub(/\r/, "", $2); print $2; exit }' .env)
    fi

    printf '%s' "${value:-$default}"
}

acceleration=$(env_value "OLLAMA_ACCELERATION" "cpu")

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

ensure_ollama_model() {
    model=$1
    if compose exec -T ollama ollama list | awk 'NR > 1 { print $1 }' | grep -Fx "$model" > /dev/null; then
        return
    fi
    printf 'Downloading Ollama model %s\n' "$model"
    compose exec -T ollama ollama pull "$model"
}

printf 'Deploying Ollama with %s acceleration\n' "$acceleration"
compose pull backend frontend nginx
compose up -d --wait database ollama

ollama_model=$(env_value "OLLAMA_MODEL" "")
embedding_provider=$(env_value "EMBEDDING_PROVIDER" "ollama")
embedding_model=$(env_value "EMBEDDING_MODEL" "embeddinggemma:300m")

if [ -n "$ollama_model" ]; then
    ensure_ollama_model "$ollama_model"
fi
if [ "$embedding_provider" = "ollama" ] && [ -n "$embedding_model" ]; then
    ensure_ollama_model "$embedding_model"
fi

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
