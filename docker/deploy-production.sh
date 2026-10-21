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
vertex_enabled=$(env_value "VERTEX_ENABLED" "false")
case "$vertex_enabled" in
    true|false) ;;
    *) printf 'VERTEX_ENABLED must be true or false\n' >&2; exit 1 ;;
esac
if [ "$vertex_enabled" = "true" ]; then
    for key in VERTEX_PROJECT VERTEX_LOCATION VERTEX_MODEL VERTEX_CREDENTIALS_FILE LITELLM_MASTER_KEY LITELLM_CPUS LITELLM_MEMORY_LIMIT; do
        test -n "$(env_value "$key" "")" || { printf 'Set %s in .env\n' "$key" >&2; exit 1; }
    done
    test -f "$(env_value VERTEX_CREDENTIALS_FILE "")" || { printf 'Vertex credential file not found\n' >&2; exit 1; }
fi

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
    if [ "$vertex_enabled" = "true" ]; then
        set -- --profile vertex "$@"
    fi
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
compose config --quiet
compose pull backend frontend nginx
compose up -d --wait database ollama
compose exec -T database sh -s < docker/postgres/migrate-database.sh
if [ "$vertex_enabled" = "true" ]; then
    compose pull litellm
    compose up -d --wait litellm
fi

ollama_model=$(env_value "OLLAMA_MODEL" "")
embedding_provider=$(env_value "EMBEDDING_PROVIDER" "ollama")
embedding_model=$(env_value "EMBEDDING_MODEL" "embeddinggemma:300m")
vision_provider=$(env_value "VISION_PROVIDER" "ollama")
vision_model=$(env_value "VISION_MODEL" "")

if [ -n "$ollama_model" ]; then
    ensure_ollama_model "$ollama_model"
fi
if [ "$embedding_provider" = "ollama" ] && [ -n "$embedding_model" ]; then
    ensure_ollama_model "$embedding_model"
fi
if [ "$vision_provider" = "ollama" ] && [ -n "$vision_model" ]; then
    ensure_ollama_model "$vision_model"
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
