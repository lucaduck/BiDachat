"""Vertex inference through the private LiteLLM Chat Completions endpoint."""

import base64

import httpx

from app.core.config import Settings
from app.llm.errors import ProviderConfigurationError, ProviderError


class VertexGateway:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def answer(
        self,
        *,
        model: str,
        prompt: str,
        instructions: str,
        image: bytes | None,
        image_mime_type: str | None,
    ) -> str:
        if not self.settings.vertex_model_available(model):
            raise ProviderConfigurationError("Vertex model is not available")
        secret = self.settings.litellm_master_key
        if secret is None:
            raise ProviderConfigurationError("Vertex gateway is not configured")

        content: list[dict] = [{"type": "text", "text": prompt}]
        if image is not None:
            if image_mime_type not in {"image/png", "image/jpeg", "image/webp"}:
                raise ProviderConfigurationError("Unsupported image MIME type")
            encoded = base64.b64encode(image).decode("ascii")
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{image_mime_type};base64,{encoded}"},
                }
            )
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": content},
            ],
            "stream": False,
            "max_tokens": 1024,
            "temperature": 0.2,
        }
        try:
            async with httpx.AsyncClient(timeout=45, trust_env=False) as client:
                response = await client.post(
                    f"{self.settings.litellm_base_url}/v1/chat/completions",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {secret.get_secret_value().strip()}"
                    },
                )
                response.raise_for_status()
        except httpx.TimeoutException:
            raise ProviderError("Vertex request timed out") from None
        except httpx.HTTPStatusError as exc:
            errors = {
                401: "Vertex authentication failed",
                403: "Vertex access denied",
                429: "Vertex quota exceeded",
            }
            raise ProviderError(
                errors.get(exc.response.status_code, "Vertex gateway unavailable")
            ) from None
        except httpx.HTTPError:
            raise ProviderError("Vertex gateway unavailable") from None

        try:
            result = response.json()
            if result["model"] not in {model, f"vertex_ai/{model}"}:
                raise ValueError("Unexpected model")
            choice = result["choices"][0]
            if choice["finish_reason"] != "stop" or choice["message"].get("refusal"):
                raise ValueError("Incomplete or blocked answer")
            answer = choice["message"]["content"].strip()
            if not answer:
                raise ValueError("Empty answer")
            return answer
        except (KeyError, IndexError, TypeError, AttributeError, ValueError):
            raise ProviderError("Invalid or incomplete Vertex response") from None
