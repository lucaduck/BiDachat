"""Build a private LiteLLM catalogue for explicitly enabled AI providers."""

import json
import os
import sys
from pathlib import Path

import yaml


SUPPORTED_PROVIDERS = frozenset({"gemini", "openai", "openrouter", "vertex"})


def configured_models(provider: str) -> list[str]:
    plural = f"{provider.upper()}_MODELS"
    singular = f"{provider.upper()}_MODEL"
    models = list(
        dict.fromkeys(
            item.strip()
            for item in os.environ.get(plural, "").split(",")
            if item.strip()
        )
    )
    return models or ([os.environ[singular].strip()] if os.environ.get(singular, "").strip() else [])


def gateway_model_alias(provider: str, model: str) -> str:
    """Keep LiteLLM routing unambiguous when providers share a model ID."""
    return f"{provider}/{model}"


def validate_vertex_credentials() -> None:
    credentials_path = Path("/run/secrets/vertex-service-account.json")
    try:
        credentials = json.loads(credentials_path.read_text())
        if credentials.get("type") != "service_account" or not all(
            credentials.get(key)
            for key in ("client_email", "private_key", "project_id")
        ):
            raise ValueError
        if credentials.get("token_uri") != "https://oauth2.googleapis.com/token":
            raise ValueError
    except (OSError, ValueError, AttributeError):
        sys.exit("Mount a valid service-account JSON as a read-only secret.")


def main() -> None:
    providers = list(
        dict.fromkeys(
            item.strip().lower()
            for item in os.environ.get("EXTERNAL_AI_GATEWAY_PROVIDERS", "").split(",")
            if item.strip()
        )
    )
    if not providers and os.environ.get("VERTEX_ENABLED", "false").lower() == "true":
        providers = ["vertex"]
    if not providers or any(provider not in SUPPORTED_PROVIDERS for provider in providers):
        sys.exit("Set EXTERNAL_AI_GATEWAY_PROVIDERS to explicit supported providers.")
    required = ("LITELLM_MASTER_KEY", "LITELLM_CPUS", "LITELLM_MEMORY_LIMIT")
    if any(not os.environ.get(name, "").strip() for name in required):
        sys.exit("Set gateway key and resource limits.")
    if len(os.environ["LITELLM_MASTER_KEY"].strip()) < 32:
        sys.exit("The gateway key must contain at least 32 characters.")
    entries: list[dict] = []
    config = yaml.safe_load(Path("/app/bidachat/config.yaml").read_text())
    for provider in providers:
        models = configured_models(provider)
        if not models:
            sys.exit(f"Configure an explicit {provider.upper()}_MODEL.")
        if provider == "vertex":
            if os.environ.get("VERTEX_ENABLED", "false").lower() != "true":
                sys.exit("Vertex gateway routing requires VERTEX_ENABLED=true.")
            if not os.environ.get("VERTEX_PROJECT", "").strip() or not os.environ.get(
                "VERTEX_LOCATION", ""
            ).strip():
                sys.exit("Set Vertex project and location.")
            validate_vertex_credentials()
            params = {
                "vertex_project": "os.environ/VERTEX_PROJECT",
                "vertex_location": "os.environ/VERTEX_LOCATION",
                "vertex_credentials": "/run/secrets/vertex-service-account.json",
            }
            prefix = "vertex_ai/"
        else:
            key_name = f"{provider.upper()}_API_KEY"
            if not os.environ.get(key_name, "").strip():
                sys.exit(f"Set {key_name} for the private gateway.")
            params = {"api_key": f"os.environ/{key_name}"}
            prefix = f"{provider}/"
        for model in models:
            entries.append(
                {
                    "model_name": gateway_model_alias(provider, model),
                    "litellm_params": {
                        "model": f"{prefix}{model}",
                        **params,
                        "max_retries": 0,
                        "timeout": 40,
                    },
                }
            )
    config["model_list"] = entries
    output = Path("/tmp/bidachat-litellm.yaml")
    output.write_text(yaml.safe_dump(config))
    output.chmod(0o600)
    os.execvp(
        "litellm",
        [
            "litellm",
            "--config",
            str(output),
            "--host",
            "0.0.0.0",
            "--port",
            "4000",
            "--num_workers",
            "1",
        ],
    )


if __name__ == "__main__":
    main()
