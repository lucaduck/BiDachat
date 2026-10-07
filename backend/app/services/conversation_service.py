from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.llm.provider import LlmProvider
from app.models import Chatbot, LlmModel
from app.services.query_service import QueryService
from app.services.rag_knowledge_service import RagKnowledgeService


class ConversationService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.provider = LlmProvider(settings)
        self.knowledge = RagKnowledgeService(settings)
        self.queries = QueryService()

    async def ask(
        self,
        session: AsyncSession,
        *,
        chatbot_id: UUID,
        question: str,
        image: bytes | None,
        image_mime_type: str | None,
        page_context: str | None = None,
    ):
        query = await self.queries.start_query(
            session,
            chatbot_id=chatbot_id,
            question=question,
            has_image=image is not None,
        )
        result = await session.execute(
            select(Chatbot.behavior_instructions, LlmModel.provider, LlmModel.model)
            .join(LlmModel, LlmModel.id == query.executed_llm_model_id)
            .where(Chatbot.id == chatbot_id)
        )
        instructions, provider, model = result.one()
        presentation_rules = (
            "Presenta la respuesta en español con párrafos breves. Si enumeras "
            "elementos sin orden, usa viñetas; reserva la numeración para pasos. "
            "Resalta solo términos cortos en negrita. Evita tablas Markdown, "
            "HTML y símbolos decorativos."
        )
        instructions = f"{instructions.strip()}\n\n{presentation_rules}".strip()
        query_id = query.id
        await session.commit()
        try:
            query_embedding = (
                await self.provider.embed(question, task_type="RETRIEVAL_QUERY")
                if (
                    self.settings.embedding_provider == "ollama"
                    or self.settings.gemini_api_key
                )
                else None
            )
            chunks = (
                await self.knowledge.retrieve_chunks(
                    session,
                    chatbot_id=chatbot_id,
                    embedding_model=self.settings.embedding_model,
                    embedding_dimensions=self.settings.embedding_dimensions,
                    query_embedding=query_embedding,
                    top_k=2 if provider == "ollama" else 5,
                )
                if query_embedding is not None
                else []
            )
            context = "\n\n".join(chunk.content for chunk in chunks)
            answer = await self.provider.answer(
                provider=provider,
                model=model,
                question=question.strip(),
                instructions=instructions,
                context=context,
                page_context=page_context or "",
                image=image,
                image_mime_type=image_mime_type,
            )
            completed = await self.queries.complete_query(
                session, query_id=query_id, answer=answer
            )
            await session.commit()
            return completed
        except Exception:
            await session.rollback()
            await self.queries.fail_query(
                session,
                query_id=query_id,
                error_code="provider_error",
                completed_at=datetime.now(UTC),
            )
            await session.commit()
            raise
