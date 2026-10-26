"""Private LiteLLM gateway for explicitly configured external providers."""

import base64

import httpx

from app.core.config import Settings
from app.llm.errors import ProviderConfigurationError, ProviderError

SUPPORTED_IMAGE_MIME_TYPES = frozenset({"image/png", "image/jpeg", "image/webp"})


def gateway_model_alias(provider: str, model: str) -> str:
    """Return the unique LiteLLM alias for a configured provider/model pair."""
    return f"{provider}/{model}"


class ExternalGateway:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def answer(
        self,
        *,
        provider: str,
        model: str,
        prompt: str,
        instructions: str,
        image: bytes | None,
        image_mime_type: str | None,
    ) -> str:
        if not self.settings.gateway_model_available(provider, model):
            raise ProviderConfigurationError("Gateway model is not available")
        secret = self.settings.litellm_master_key
        if secret is None or not secret.get_secret_value().strip():
            raise ProviderConfigurationError("External AI gateway is not configured")

        if provider == "openai":
            payload = self._openai_responses_payload(
                gateway_model_alias(provider, model),
                prompt,
                instructions,
                image,
                image_mime_type,
            )
            result = await self._post("/v1/responses", payload, secret)
            return self._read_openai_response(result, model)

        payload = self._chat_payload(
            gateway_model_alias(provider, model),
            prompt,
            instructions,
            image,
            image_mime_type,
        )
        result = await self._post("/v1/chat/completions", payload, secret)
        return self._read_chat_response(result, model, provider)

    @staticmethod
    def _encoded_image(image: bytes, image_mime_type: str | None) -> str:
        if image_mime_type not in SUPPORTED_IMAGE_MIME_TYPES:
            raise ProviderConfigurationError("Unsupported image MIME type")
        return (
            f"data:{image_mime_type};base64,{base64.b64encode(image).decode('ascii')}"
        )

    def _openai_responses_payload(
        self,
        model: str,
        prompt: str,
        instructions: str,
        image: bytes | None,
        image_mime_type: str | None,
    ) -> dict:
        content: list[dict] = [{"type": "input_text", "text": prompt}]
        if image is not None:
            content.append(
                {
                    "type": "input_image",
                    "image_url": self._encoded_image(image, image_mime_type),
                }
            )
        payload: dict = {
            "model": model,
            "input": [{"role": "user", "content": content}],
            "store": False,
        }
        if instructions:
            payload["instructions"] = instructions
        return payload

    def _chat_payload(
        self,
        model: str,
        prompt: str,
        instructions: str,
        image: bytes | None,
        image_mime_type: str | None,
    ) -> dict:
        content: str | list[dict] = prompt
        if image is not None:
            content = [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": self._encoded_image(image, image_mime_type)},
                },
            ]
        messages: list[dict] = []
        if instructions:
            messages.append({"role": "system", "content": instructions})
        messages.append({"role": "user", "content": content})
        return {
            "model": model,
            "messages": messages,
            "stream": False,
            "max_tokens": 1024,
            "temperature": 0.2,
        }

    async def _post(self, path: str, payload: dict, secret) -> dict:
        try:
            async with httpx.AsyncClient(timeout=45, trust_env=False) as client:
                response = await client.post(
                    f"{self.settings.litellm_base_url}{path}",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {secret.get_secret_value().strip()}"
                    },
                )
                response.raise_for_status()
                result = response.json()
                if not isinstance(result, dict):
                    raise ProviderError("Invalid or incomplete gateway response")
                return result
        except httpx.TimeoutException:
            raise ProviderError("External AI gateway request timed out") from None
        except httpx.HTTPStatusError as exc:
            errors = {
                401: "External AI gateway authentication failed",
                403: "External AI gateway access denied",
                429: "External AI gateway quota exceeded",
            }
            raise ProviderError(
                errors.get(exc.response.status_code, "External AI gateway unavailable")
            ) from None
        except (httpx.HTTPError, ValueError):
            raise ProviderError("External AI gateway unavailable") from None

    @staticmethod
    def _read_openai_response(result: dict, model: str) -> str:
        try:
            if result.get("model") not in {model, gateway_model_alias("openai", model)}:
                raise ValueError
            if result.get("status") != "completed":
                raise ValueError
            answer = "".join(
                part["text"]
                for item in result["output"]
                if item.get("type") == "message"
                for part in item["content"]
                if part.get("type") == "output_text"
            ).strip()
            if not answer:
                raise ValueError
            return answer
        except (KeyError, TypeError, AttributeError, ValueError):
            raise ProviderError("Invalid or incomplete gateway response") from None

    @staticmethod
    def _read_chat_response(result: dict, model: str, provider: str) -> str:
        expected_models = {model, gateway_model_alias(provider, model)}
        if provider == "vertex":
            expected_models.add(f"vertex_ai/{model}")
        try:
            if result["model"] not in expected_models:
                raise ValueError
            choice = result["choices"][0]
            if choice["finish_reason"] != "stop" or choice["message"].get("refusal"):
                raise ValueError
            answer = choice["message"]["content"].strip()
            if not answer:
                raise ValueError
            return answer
        except (KeyError, IndexError, TypeError, AttributeError, ValueError):
            raise ProviderError("Invalid or incomplete gateway response") from None
