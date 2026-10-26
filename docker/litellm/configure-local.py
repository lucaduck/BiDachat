"""Configure local Vertex variables without printing or copying credentials."""

import argparse
import json
import re
import secrets
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--credentials", required=True, type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--location", default="global")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    credentials = args.credentials.resolve(strict=True)
    if credentials.is_relative_to(root):
        parser.error("Store Google credentials outside the repository.")
    data = json.loads(credentials.read_text())
    if data.get("type") != "service_account" or not data.get("private_key"):
        parser.error("Expected a service-account JSON file.")
    if not re.fullmatch(r"gemini-[a-zA-Z0-9.-]+", args.model):
        parser.error("Use an explicit Gemini model ID.")
    env_file = root / ".env"
    content = env_file.read_text()
    existing = dict(re.findall(r"^([A-Z_]+)=(.*)$", content, re.MULTILINE))
    providers = [
        item
        for item in existing.get("EXTERNAL_AI_GATEWAY_PROVIDERS", "").split(",")
        if item
    ]
    if "vertex" not in providers:
        providers.append("vertex")
    profiles = [
        item for item in existing.get("COMPOSE_PROFILES", "").split(",") if item
    ]
    if "ai-gateway" not in profiles:
        profiles.append("ai-gateway")
    values = {
        "VERTEX_ENABLED": "true",
        "EXTERNAL_AI_GATEWAY_PROVIDERS": ",".join(providers),
        "COMPOSE_PROFILES": ",".join(profiles),
        "VERTEX_PROJECT": data["project_id"],
        "VERTEX_LOCATION": args.location,
        "VERTEX_MODEL": args.model,
        "VERTEX_MODELS": existing.get("VERTEX_MODELS") or args.model,
        "VERTEX_CREDENTIALS_FILE": str(credentials),
        "LITELLM_MASTER_KEY": existing.get("LITELLM_MASTER_KEY")
        or "sk-" + secrets.token_hex(32),
        "LITELLM_CPUS": existing.get("LITELLM_CPUS") or "1",
        "LITELLM_MEMORY_LIMIT": existing.get("LITELLM_MEMORY_LIMIT") or "1g",
    }
    for name, value in values.items():
        if "\n" in value or "\r" in value or "'" in value:
            parser.error(f"Unsupported characters in {name}.")
        line = f"{name}='{value}'" if " " in value else f"{name}={value}"
        pattern = rf"^{name}=.*$"
        if re.search(pattern, content, re.MULTILINE):
            content = re.sub(
                pattern, lambda _, line=line: line, content, flags=re.MULTILINE
            )
        else:
            content = content.rstrip() + "\n" + line + "\n"
    env_file.write_text(content)
    print("Local Vertex configuration saved. Credentials were not copied.")
    print(
        f"Project: {data['project_id']}; model: {args.model}; location: {args.location}"
    )


if __name__ == "__main__":
    main()
