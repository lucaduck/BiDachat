"""Validate local configuration before starting the private Vertex gateway."""

import json
import os
import re
import sys
from pathlib import Path

import yaml


def main() -> None:
    required = (
        "VERTEX_PROJECT",
        "VERTEX_LOCATION",
        "VERTEX_MODEL",
        "LITELLM_MASTER_KEY",
        "LITELLM_CPUS",
        "LITELLM_MEMORY_LIMIT",
    )
    if any(not os.environ.get(name, "").strip() for name in required):
        sys.exit(
            "Set Vertex project, location, model, gateway key and resource limits."
        )
    if len(os.environ["LITELLM_MASTER_KEY"].strip()) < 32:
        sys.exit("The gateway key must contain at least 32 characters.")
    default_model = os.environ["VERTEX_MODEL"].strip()
    models = list(
        dict.fromkeys(
            item.strip()
            for item in os.environ.get("VERTEX_MODELS", "").split(",")
            if item.strip()
        )
    ) or [default_model]
    if default_model not in models or any(
        not re.fullmatch(r"gemini-[a-zA-Z0-9.-]+", model) for model in models
    ):
        sys.exit("VERTEX_MODELS must contain VERTEX_MODEL and explicit Gemini IDs.")
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
    config = yaml.safe_load(Path("/app/bidachat/config.yaml").read_text())
    template = config["model_list"][0]["litellm_params"]
    config["model_list"] = [
        {
            "model_name": model,
            "litellm_params": template | {"model": f"vertex_ai/{model}"},
        }
        for model in models
    ]
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
