"""Run isolated, real RAG acceptance checks against the local API and database.

Run inside the backend container with --image-dir pointing to three generated
PNG, JPEG, and WebP fixtures. This script never selects or changes user data.
"""

import argparse
import asyncio
import json
import secrets
import sys
import traceback
from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4

import httpx
from docx import Document as WordDocument
from sqlalchemy import delete, func, select

from app.core.config import get_settings
from app.core.security import hash_password
from app.database.session import Database
from app.llm.provider import LlmProvider
from app.models import Chatbot, Document, DocumentChunk, LlmModel, Query, User
from app.services.rag_knowledge_service import RagKnowledgeService

API_ROOT = "http://127.0.0.1:8000/api/v1"


def make_pdf(text: str) -> bytes:
    """Build a small valid PDF with selectable text and no external library."""
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 18 Tf 72 720 Td ({escaped}) Tj ET".encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length "
        + str(len(stream)).encode()
        + b" >>\nstream\n"
        + stream
        + b"\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, body in enumerate(objects, 1):
        offsets.append(len(output))
        output += f"{index} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(output)
    output += f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode()
    output += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:])
    output += (
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n"
    ).encode()
    return bytes(output)


def make_docx(text: str) -> bytes:
    document = WordDocument()
    document.add_paragraph(text)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


class AcceptanceRun:
    def __init__(self, image_dir: Path) -> None:
        self.settings = get_settings()
        self.database = Database.from_settings(self.settings)
        self.image_dir = image_dir
        self.run_id = uuid4()
        self.user_id = self.run_id
        self.email = f"acceptance-qa-{self.run_id}@bidachat.test"
        self.password = secrets.token_urlsafe(24)
        self.bot_ids: list[UUID] = []
        self.temporary_model_ids: list[UUID] = []
        self.results: list[dict] = []
        self.client = httpx.AsyncClient(base_url=API_ROOT, timeout=700)
        self.model_id: UUID | None = None

    def record(self, task: str, case: str, **details: object) -> None:
        self.results.append({"task": task, "case": case, "result": "passed", **details})
        print(f"PASS {task} {case}", file=sys.stderr, flush=True)

    async def request(self, method: str, path: str, expected: int, **kwargs):
        response = await self.client.request(method, path, **kwargs)
        if response.status_code != expected:
            raise AssertionError(
                f"{method} {path}: expected {expected}, "
                f"received {response.status_code}; "
                f"body={response.text[:250]}"
            )
        return response

    async def setup(self) -> None:
        async with self.database.session() as session:
            model = await session.scalar(
                select(LlmModel).where(
                    LlmModel.provider == "ollama",
                    LlmModel.model == self.settings.ollama_model,
                )
            )
            if model is None:
                raise RuntimeError(
                    "The configured local vision model is not registered"
                )
            self.model_id = model.id
            session.add(
                User(
                    id=self.user_id,
                    email=self.email,
                    password_hash=hash_password(self.password),
                )
            )
            await session.commit()
        response = await self.request(
            "POST",
            "/auth/login",
            200,
            json={"email": self.email, "password": self.password},
        )
        self.client.headers["Authorization"] = (
            f"Bearer {response.json()['access_token']}"
        )
        self.record("3.1", "isolated-user-created", run_id=str(self.run_id))

    async def create_bot(self, label: str, model_id: UUID | None = None) -> UUID:
        response = await self.request(
            "POST",
            "/chatbots",
            201,
            json={
                "name": f"RAG QA {self.run_id} {label}",
                "configured_llm_model_id": str(model_id or self.model_id),
                "behavior_instructions": "Responde brevemente en español.",
            },
        )
        identifier = UUID(response.json()["id"])
        self.bot_ids.append(identifier)
        return identifier

    async def upload(
        self,
        bot_id: UUID,
        filename: str,
        media_type: str,
        content: bytes,
        expected: int = 201,
    ):
        return await self.request(
            "POST",
            f"/chatbots/{bot_id}/documents",
            expected,
            files={"file": (filename, content, media_type)},
        )

    async def verify_source(
        self, bot_id: UUID, document_id: UUID, marker: str, task: str, case: str
    ) -> None:
        async with self.database.session() as session:
            document = await session.get(Document, document_id)
            assert document is not None and document.status == "ready"
            chunks = list(
                await session.scalars(
                    select(DocumentChunk).where(
                        DocumentChunk.document_id == document_id
                    )
                )
            )
            assert chunks and all(len(chunk.embedding) == 768 for chunk in chunks)
            description = " ".join(chunk.content for chunk in chunks)
            assert marker.lower() in description.lower(), (
                f"{case}: marker {marker!r} absent from extracted content: "
                f"{description[:300]!r}"
            )
            embedding = await LlmProvider(self.settings).embed(
                f"¿Qué indica {marker}?", task_type="RETRIEVAL_QUERY"
            )
            retrieved = await RagKnowledgeService(self.settings).retrieve_chunks(
                session,
                chatbot_id=bot_id,
                embedding_model=self.settings.embedding_model,
                embedding_dimensions=768,
                query_embedding=embedding,
            )
            assert any(item.document_id == document_id for item in retrieved)
            self.record(
                task,
                case,
                document_id=str(document_id),
                status=document.status,
                chunks=len(chunks),
                dimensions=768,
                marker_found=True,
                retrieval_hits=len(retrieved),
            )

    async def sources(self) -> dict[str, tuple[UUID, UUID]]:
        source_data = [
            ("pdf", "application/pdf", make_pdf("CLAVE PDF ALFA 17"), "ALFA 17"),
            (
                "docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                make_docx("CLAVE DOCX BETA 28"),
                "BETA 28",
            ),
            ("txt", "text/plain", b"CLAVE TXT GAMMA 39", "GAMMA 39"),
            ("csv", "text/csv", b"categoria,valor\nDELTA,46\n", "DELTA"),
            (
                "png",
                "image/png",
                (self.image_dir / "source-png.png").read_bytes(),
                "41",
            ),
            (
                "jpg",
                "image/jpeg",
                (self.image_dir / "source-jpg.jpg").read_bytes(),
                "52",
            ),
            (
                "webp",
                "image/webp",
                (self.image_dir / "source-webp.webp").read_bytes(),
                "63",
            ),
        ]
        created = {}
        for extension, media_type, data, marker in source_data:
            bot_id = await self.create_bot(extension)
            response = await self.upload(
                bot_id, f"source.{extension}", media_type, data
            )
            body = response.json()
            document_id = UUID(body["id"])
            await self.verify_source(
                bot_id,
                document_id,
                marker,
                "3.3" if extension in {"png", "jpg", "webp"} else "3.2",
                extension,
            )
            created[extension] = (bot_id, document_id)
        return created

    async def invalid_sources(self, bot_id: UUID) -> None:
        cases = [
            ("corrupt-pdf", "broken.pdf", "application/pdf", b"%PDF-corrupt", 201),
            ("misleading-type", "fake.pdf", "text/plain", b"%PDF-1.4", 422),
            (
                "oversize",
                "large.txt",
                "text/plain",
                b"x" * (self.settings.document_max_size_bytes + 1),
                422,
            ),
            ("image-signature", "fake.png", "image/png", b"not an image", 422),
            ("textless-pdf", "blank.pdf", "application/pdf", make_pdf(""), 201),
        ]
        for label, filename, media_type, data, expected in cases:
            response = await self.upload(bot_id, filename, media_type, data, expected)
            if expected == 201:
                body = response.json()
                assert body["status"] == "failed", f"{label}: {body}"
                async with self.database.session() as session:
                    count = await session.scalar(
                        select(func.count(DocumentChunk.id)).where(
                            DocumentChunk.document_id == UUID(body["id"])
                        )
                    )
                    assert count == 0
                self.record(
                    "3.4",
                    label,
                    http_status=expected,
                    document_status="failed",
                    error_code=body["error_code"],
                    chunks=0,
                )
            else:
                self.record("3.4", label, http_status=expected, rejected=True)

    async def shared_source(
        self, source_bot: UUID, document_id: UUID, label: str
    ) -> None:
        other_bot = await self.create_bot(f"shared-{label}")
        await self.request(
            "POST",
            f"/chatbots/{other_bot}/documents/associations",
            200,
            json={"document_ids": [str(document_id)]},
        )
        embedding = await LlmProvider(self.settings).embed(
            f"Contenido de la fuente {label}", task_type="RETRIEVAL_QUERY"
        )
        service = RagKnowledgeService(self.settings)
        async with self.database.session() as session:

            async def retrieved(bot_id: UUID):
                return await service.retrieve_chunks(
                    session,
                    chatbot_id=bot_id,
                    embedding_model=self.settings.embedding_model,
                    embedding_dimensions=768,
                    query_embedding=embedding,
                )

            assert any(
                item.document_id == document_id for item in await retrieved(source_bot)
            )
            assert any(
                item.document_id == document_id for item in await retrieved(other_bot)
            )
        await self.request(
            "DELETE", f"/chatbots/{source_bot}/documents/{document_id}", 204
        )
        async with self.database.session() as session:
            for bot_id, expected in [(source_bot, False), (other_bot, True)]:
                hits = await service.retrieve_chunks(
                    session,
                    chatbot_id=bot_id,
                    embedding_model=self.settings.embedding_model,
                    embedding_dimensions=768,
                    query_embedding=embedding,
                )
                assert any(item.document_id == document_id for item in hits) == expected
            assert await session.get(Document, document_id) is not None
        self.record(
            "3.5",
            label,
            source_removed=True,
            shared_document_retained=True,
            other_bot_retrieves=True,
        )

    async def metrics_after_model_change(self) -> None:
        async with self.database.session() as session:
            success_model = await session.scalar(
                select(LlmModel).where(
                    LlmModel.provider == "openai",
                    LlmModel.model == self.settings.openai_model,
                )
            )
        if success_model is None or self.settings.openai_api_key is None:
            raise RuntimeError("The configured OpenAI model is required for this check")
        bot_id = await self.create_bot("metrics", success_model.id)
        response = await self.request(
            "POST",
            f"/chatbots/{bot_id}/queries",
            200,
            json={"question": "Responde solo: prueba completada"},
        )
        completed_id = UUID(response.json()["id"])
        missing_model = LlmModel(provider="ollama", model=f"qa-missing-{self.run_id}")
        async with self.database.session() as session:
            session.add(missing_model)
            await session.commit()
            self.temporary_model_ids.append(missing_model.id)
        await self.request(
            "PUT",
            f"/chatbots/{bot_id}",
            200,
            json={
                "name": f"RAG QA {self.run_id} metrics",
                "configured_llm_model_id": str(missing_model.id),
                "behavior_instructions": "Responde brevemente en español.",
            },
        )
        await self.request(
            "POST",
            f"/chatbots/{bot_id}/queries",
            503,
            json={"question": "Esta consulta debe fallar de forma segura"},
        )
        async with self.database.session() as session:
            queries = list(
                await session.scalars(
                    select(Query)
                    .where(Query.chatbot_id == bot_id)
                    .order_by(Query.received_at)
                )
            )
            assert len(queries) == 2
            completed = next(item for item in queries if item.id == completed_id)
            failed = next(item for item in queries if item.id != completed_id)
            assert (
                completed.status == "completed"
                and completed.executed_llm_model_id == success_model.id
            )
            assert (
                failed.status == "failed"
                and failed.executed_llm_model_id == missing_model.id
            )
            assert (
                completed.response_time_ms is not None
                and completed.response_time_ms >= 0
            )
            assert failed.response_time_ms is not None and failed.response_time_ms >= 0
            start = min(item.received_at for item in queries) - timedelta(minutes=1)
            end = datetime.now(UTC) + timedelta(minutes=1)
            params = {
                "started_at": start.isoformat(),
                "ended_at": end.isoformat(),
                "include_series": "true",
            }
            response = await self.request(
                "GET", f"/chatbots/{bot_id}/metrics", 200, params=params
            )
            values = response.json()
            assert values["total_queries"] == 2
            assert values["completed_queries"] == 1
            assert values["failed_queries"] == 1
            assert values["measured_response_count"] == 1
            assert values["average_response_time_ms"] == completed.response_time_ms
            self.record(
                "3.7",
                "model-change-and-metrics",
                completed_ms=completed.response_time_ms,
                failed_ms=failed.response_time_ms,
                total=2,
                completed=1,
                failed=1,
                completed_model=success_model.model,
                failed_model=missing_model.model,
            )

    async def cleanup(self) -> None:
        async with self.database.session() as session:
            user = await session.get(User, self.user_id)
            if user is None:
                return
            if user.email != self.email:
                raise RuntimeError("Fixture identity changed; cleanup refused")
            owned_bots = select(Chatbot.id).where(Chatbot.created_by == self.user_id)
            files = list(
                await session.scalars(
                    select(Document.storage_key).where(
                        Document.chatbot_id.in_(owned_bots)
                    )
                )
            )
            await session.execute(
                delete(Chatbot).where(Chatbot.created_by == self.user_id)
            )
            await session.delete(user)
            if self.temporary_model_ids:
                await session.execute(
                    delete(LlmModel).where(LlmModel.id.in_(self.temporary_model_ids))
                )
            await session.commit()
        root = self.settings.document_storage_path.resolve()
        for key in files:
            path = (root / Path(key).name).resolve()
            if not path.is_relative_to(root):
                raise RuntimeError("Fixture file path escaped storage root")
            path.unlink(missing_ok=True)
        self.record("3.1", "cleanup", bots=len(self.bot_ids), files=len(files))

    async def run(self, phase: str) -> None:
        failure = None
        try:
            await self.setup()
            if phase in {"all", "sources"}:
                sources = await self.sources()
                await self.invalid_sources(sources["txt"][0])
                await self.shared_source(*sources["txt"], "text")
                await self.shared_source(*sources["png"], "visual")
            if phase in {"all", "metrics"}:
                await self.metrics_after_model_change()
        except Exception as exc:
            failure = {
                "type": type(exc).__name__,
                "detail": str(exc)[:500],
                "traceback": traceback.format_exc(limit=3),
            }
            print(
                f"FAIL {failure['type']}: {failure['detail']}",
                file=sys.stderr,
                flush=True,
            )
        finally:
            try:
                await self.cleanup()
            except Exception as exc:
                failure = failure or {}
                failure["cleanup_error"] = f"{type(exc).__name__}: {str(exc)[:300]}"
            await self.client.aclose()
            await self.database.dispose()
            print(
                json.dumps(
                    {
                        "run_id": str(self.run_id),
                        "results": self.results,
                        "failure": failure,
                    },
                    ensure_ascii=False,
                )
            )
        if failure:
            raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-dir", type=Path, required=True)
    parser.add_argument("--phase", choices=["all", "sources", "metrics"], default="all")
    arguments = parser.parse_args()
    asyncio.run(AcceptanceRun(arguments.image_dir).run(arguments.phase))
