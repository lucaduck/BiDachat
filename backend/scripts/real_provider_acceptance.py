"""Check configured external AI adapters with small synthetic text and image calls."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from app.core.config import get_settings
from app.llm.provider import LlmProvider, ProviderError


async def check(provider: str, model: str, image: bytes | None) -> dict:
    settings = get_settings()
    adapter = LlmProvider(settings)
    original_post = adapter._post
    usage: dict = {}

    async def capture_post(url: str, payload: dict, headers: dict[str, str]) -> dict:
        response = await original_post(url, payload, headers)
        usage.update(response.get("usage") or {})
        return response

    adapter._post = capture_post
    modality = "image" if image is not None else "text"
    try:
        answer = await adapter.answer(
            provider=provider,
            model=model,
            question=(
                "Lee el número grande de esta imagen. Responde solo el número."
                if image is not None
                else "Responde únicamente con la palabra listo."
            ),
            instructions="Respuesta breve en español.",
            context="",
            image=image,
            image_mime_type="image/png" if image is not None else None,
        )
        expected = "41" if image is not None else "listo"
        return {
            "provider": provider,
            "model": model,
            "modality": modality,
            "result": "passed" if expected in answer.lower() else "content-mismatch",
            "answer_length": len(answer),
            "expected_marker_found": expected in answer.lower(),
            "usage": usage,
        }
    except ProviderError as exc:
        return {
            "provider": provider,
            "model": model,
            "modality": modality,
            "result": "failed",
            "error_type": type(exc).__name__,
        }


async def run(image_path: Path) -> None:
    settings = get_settings()
    image = image_path.read_bytes()
    results = []
    estimated_cost_usd = 0.0
    for provider, model, key in [
        ("gemini", "", settings.gemini_api_key),
        ("openai", settings.openai_model, settings.openai_api_key),
        ("openrouter", settings.openrouter_model, settings.openrouter_api_key),
    ]:
        if key is None or not key.get_secret_value().strip():
            results.extend(
                {
                    "provider": provider,
                    "model": model or None,
                    "modality": modality,
                    "result": "blocked-no-key",
                }
                for modality in ("text", "image")
            )
            continue
        if provider == "openrouter":
            # The configured slug is checked as-is; the free router is an
            # isolated compatibility probe, not a persistent model change.
            results.append(await check(provider, model, None))
            model = "openrouter/free"
        for payload in (None, image):
            if estimated_cost_usd >= 0.90:
                results.append(
                    {
                        "provider": provider,
                        "model": model,
                        "modality": "image" if payload else "text",
                        "result": "blocked-budget",
                    }
                )
                continue
            result = await check(provider, model, payload)
            results.append(result)
            if provider == "openai":
                usage = result.get("usage", {})
                if result["result"] == "passed" and not usage:
                    raise RuntimeError(
                        "OpenAI usage is missing; spending cannot be measured"
                    )
                estimated_cost_usd += (
                    (usage.get("input_tokens", 0) * 0.20)
                    + (usage.get("output_tokens", 0) * 1.20)
                ) / 1_000_000
            print(
                f"{provider} {model} {result['modality']}: {result['result']}",
                file=sys.stderr,
                flush=True,
            )
    print(
        json.dumps(
            {
                "budget_usd": 1.0,
                "estimated_openai_cost_usd": estimated_cost_usd,
                "results": results,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True)
    arguments = parser.parse_args()
    asyncio.run(run(arguments.image))
