import base64
from math import isfinite

import httpx

from app.core.config import Settings


class ProviderError(Exception):
    pass


class ProviderConfigurationError(ProviderError):
    pass


class LlmProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def answer(
        self,
        *,
        provider: str,
        model: str,
        question: str,
        instructions: str,
        context: str,
        image: bytes | None,
        image_mime_type: str | None,
    ) -> str:
        prompt = (
            f"Question from the dashboard user:\n{question}\n\n"
            "Relevant chatbot documents (may be empty):\n"
            f"{context or 'No documents available.'}\n\n"
            "Use the documents only when relevant. If the documents do not support a "
            "specific claim, say so rather than inventing one."
        )
        if provider == "gemini":
            return await self._gemini_answer(
                model, prompt, instructions, image, image_mime_type
            )
        if provider == "ollama":
            return await self._ollama_answer(model, prompt, instructions, image)
        if provider == "openai":
            return await self._openai_answer(
                model, prompt, instructions, image, image_mime_type
            )
        if provider == "openrouter":
            return await self._openrouter_answer(
                model, prompt, instructions, image, image_mime_type
            )
        raise ProviderConfigurationError("Unsupported LLM provider")

    async def embed(self, text: str, *, task_type: str) -> list[float]:
        if task_type == "RETRIEVAL_QUERY":
            formatted_text = f"task: question answering | query: {text}"
        elif task_type == "RETRIEVAL_DOCUMENT":
            formatted_text = f"title: none | text: {text}"
        else:
            raise ValueError("Unsupported embedding task")
        if self.settings.embedding_provider == "ollama":
            result = await self._post(
                f"{self.settings.ollama_base_url}/api/embed",
                {
                    "model": self.settings.embedding_model,
                    "input": formatted_text,
                    "dimensions": self.settings.embedding_dimensions,
                    "truncate": False,
                    "keep_alive": 0,
                },
                {},
            )
        else:
            result = await self._post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{self.settings.embedding_model}:embedContent",
                {
                    "model": f"models/{self.settings.embedding_model}",
                    "content": {"parts": [{"text": formatted_text}]},
                    "output_dimensionality": self.settings.embedding_dimensions,
                },
                {"x-goog-api-key": self._gemini_key()},
            )
        try:
            raw = (
                result["embeddings"][0]
                if self.settings.embedding_provider == "ollama"
                else result["embedding"]["values"]
            )
            values = [float(value) for value in raw]
            if (
                len(values) != self.settings.embedding_dimensions
                or not all(isfinite(value) for value in values)
                or not any(values)
            ):
                raise ValueError("Invalid embedding vector")
            return values
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderError("Invalid embedding response") from exc

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if self.settings.embedding_provider != "ollama":
            return [
                await self.embed(text, task_type="RETRIEVAL_DOCUMENT") for text in texts
            ]
        vectors: list[list[float]] = []
        for offset in range(0, len(texts), 16):
            batch = texts[offset : offset + 16]
            result = await self._post(
                f"{self.settings.ollama_base_url}/api/embed",
                {
                    "model": self.settings.embedding_model,
                    "input": [f"title: none | text: {text}" for text in batch],
                    "dimensions": self.settings.embedding_dimensions,
                    "truncate": False,
                    "keep_alive": 0,
                },
                {},
            )
            try:
                raw = result["embeddings"]
                if len(raw) != len(batch):
                    raise ValueError("Unexpected vector count")
                for vector in raw:
                    values = [float(value) for value in vector]
                    if (
                        len(values) != self.settings.embedding_dimensions
                        or not all(isfinite(value) for value in values)
                        or not any(values)
                    ):
                        raise ValueError("Invalid embedding vector")
                    vectors.append(values)
            except (KeyError, TypeError, ValueError) as exc:
                raise ProviderError("Invalid embedding response") from exc
        return vectors

    async def validate_ollama_model(self, model: str, *, has_image: bool) -> None:
        result = await self._post(
            f"{self.settings.ollama_base_url}/api/show", {"model": model}, {}
        )
        capabilities = result.get("capabilities", [])
        if "completion" not in capabilities or (
            has_image and "vision" not in capabilities
        ):
            raise ProviderConfigurationError("Model does not support this input")

    async def _gemini_answer(
        self,
        model: str,
        prompt: str,
        instructions: str,
        image: bytes | None,
        image_mime_type: str | None,
    ) -> str:
        parts: list[dict] = [{"text": prompt}]
        if image is not None:
            parts.append(
                {
                    "inline_data": {
                        "mime_type": image_mime_type,
                        "data": base64.b64encode(image).decode("ascii"),
                    }
                }
            )
        payload: dict = {"contents": [{"role": "user", "parts": parts}]}
        if instructions:
            payload["systemInstruction"] = {"parts": [{"text": instructions}]}
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        result = await self._post(url, payload, {"x-goog-api-key": self._gemini_key()})
        try:
            answer = "".join(
                part.get("text", "")
                for part in result["candidates"][0]["content"]["parts"]
            ).strip()
            if not answer:
                raise ValueError("Empty answer")
            return answer
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderError("Invalid Gemini response") from exc

    async def _ollama_answer(
        self, model: str, prompt: str, instructions: str, image: bytes | None
    ) -> str:
        await self.validate_ollama_model(model, has_image=image is not None)
        message: dict = {"role": "user", "content": prompt}
        if image is not None:
            message["images"] = [base64.b64encode(image).decode("ascii")]
        messages = (
            [{"role": "system", "content": instructions}] if instructions else []
        ) + [message]
        result = await self._post(
            f"{self.settings.ollama_base_url.rstrip('/')}/api/chat",
            {
                "model": model,
                "messages": messages,
                "stream": False,
                "think": False,
                "keep_alive": 0,
                "options": {
                    "num_ctx": self.settings.ollama_context_length,
                    "num_predict": 512,
                    "temperature": 0.2,
                },
            },
            {},
        )
        try:
            answer = result["message"]["content"].strip()
            if not answer:
                raise ValueError("Empty answer")
            return answer
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderError("Invalid Ollama response") from exc

    async def _openai_answer(
        self,
        model: str,
        prompt: str,
        instructions: str,
        image: bytes | None,
        image_mime_type: str | None,
    ) -> str:
        secret = self.settings.openai_api_key
        if secret is None or not secret.get_secret_value().strip():
            raise ProviderConfigurationError("OpenAI API key is not configured")
        content: list[dict] = [{"type": "input_text", "text": prompt}]
        if image is not None:
            if image_mime_type not in {"image/png", "image/jpeg", "image/webp"}:
                raise ProviderConfigurationError("Unsupported image MIME type")
            encoded_image = base64.b64encode(image).decode("ascii")
            content.append(
                {
                    "type": "input_image",
                    "image_url": f"data:{image_mime_type};base64,{encoded_image}",
                }
            )
        payload: dict = {
            "model": model,
            "input": [{"role": "user", "content": content}],
            "store": False,
        }
        if instructions:
            payload["instructions"] = instructions
        result = await self._post(
            "https://api.openai.com/v1/responses",
            payload,
            {"Authorization": f"Bearer {secret.get_secret_value().strip()}"},
        )
        try:
            if result.get("status") != "completed":
                raise ValueError("Response did not complete")
            answer = "".join(
                part["text"]
                for item in result["output"]
                if item.get("type") == "message"
                for part in item["content"]
                if part.get("type") == "output_text"
            ).strip()
            if not answer:
                raise ValueError("Empty answer")
            return answer
        except (KeyError, TypeError, AttributeError, ValueError) as exc:
            raise ProviderError("Invalid OpenAI response") from exc

    async def _openrouter_answer(
        self,
        model: str,
        prompt: str,
        instructions: str,
        image: bytes | None,
        image_mime_type: str | None,
    ) -> str:
        secret = self.settings.openrouter_api_key
        if secret is None or not secret.get_secret_value().strip():
            raise ProviderConfigurationError("OpenRouter API key is not configured")

        content: str | list[dict] = prompt
        if image is not None:
            if image_mime_type not in {"image/png", "image/jpeg", "image/webp"}:
                raise ProviderConfigurationError("Unsupported image MIME type")
            encoded_image = base64.b64encode(image).decode("ascii")
            content = [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{image_mime_type};base64,{encoded_image}"
                    },
                },
            ]

        messages: list[dict] = []
        if instructions:
            messages.append({"role": "system", "content": instructions})
        messages.append({"role": "user", "content": content})
        headers = {"Authorization": f"Bearer {secret.get_secret_value().strip()}"}
        if self.settings.openrouter_site_url.strip():
            headers["HTTP-Referer"] = self.settings.openrouter_site_url.strip()
        headers["X-OpenRouter-Title"] = "BIDACHAT"
        result = await self._post(
            "https://openrouter.ai/api/v1/chat/completions",
            {
                "model": model,
                "messages": messages,
                "max_tokens": 512,
                "temperature": 0.2,
            },
            headers,
        )
        try:
            answer = result["choices"][0]["message"]["content"].strip()
            if not answer:
                raise ValueError("Empty answer")
            return answer
        except (KeyError, IndexError, TypeError, AttributeError, ValueError) as exc:
            raise ProviderError("Invalid OpenRouter response") from exc

    def _gemini_key(self) -> str:
        if self.settings.gemini_api_key is None:
            raise ProviderConfigurationError("Gemini API key is not configured")
        key = self.settings.gemini_api_key.get_secret_value().strip()
        if not key:
            raise ProviderConfigurationError("Gemini API key is not configured")
        return key

    async def _post(self, url: str, payload: dict, headers: dict[str, str]) -> dict:
        try:
            async with httpx.AsyncClient(
                timeout=(
                    self.settings.ollama_timeout_seconds
                    if url.startswith(self.settings.ollama_base_url + "/")
                    else 45
                )
            ) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                if not isinstance(result, dict):
                    raise ValueError("Response is not an object")
                return result
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderError("LLM provider request failed") from exc
