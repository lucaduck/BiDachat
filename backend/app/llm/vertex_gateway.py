"""Backward-compatible Vertex facade for the private external AI gateway."""

from app.core.config import Settings
from app.llm.external_gateway import ExternalGateway


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
        return await ExternalGateway(self.settings).answer(
            provider="vertex",
            model=model,
            prompt=prompt,
            instructions=instructions,
            image=image,
            image_mime_type=image_mime_type,
        )
