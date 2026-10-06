import asyncio
import sys
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.core.config import Settings
from app.core.security import hash_password
from app.main import create_app
from app.models import Chatbot, LlmModel, User
from app.services.document_service import (
    DocumentService,
    DocumentUploadValidationError,
    UploadDocument,
)


def _docx_content() -> bytes:
    content = BytesIO()
    with ZipFile(content, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types />")
    return content.getvalue()


def test_document_validation_supports_approved_formats(tmp_path: Path):
    service = DocumentService(Settings(document_storage_path=tmp_path))
    uploads = [
        UploadDocument("report.pdf", "application/pdf", b"%PDF-1.7\ncontent"),
        UploadDocument(
            "report.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            _docx_content(),
        ),
        UploadDocument("report.txt", "text/plain", b"Contenido UTF-8"),
        UploadDocument("report.csv", "text/csv", b"metric,value\nqueries,10\n"),
        UploadDocument("chart.png", "image/png", b"\x89PNG\r\n\x1a\nimage"),
        UploadDocument("chart.jpg", "image/jpeg", b"\xff\xd8\xffimage"),
        UploadDocument("chart.webp", "image/webp", b"RIFFxxxxWEBPimage"),
    ]

    for upload in uploads:
        assert service._validate_upload(upload)[0] == upload.filename

    with pytest.raises(DocumentUploadValidationError):
        service._validate_upload(
            UploadDocument("malware.exe", "application/octet-stream", b"binary")
        )
    with pytest.raises(DocumentUploadValidationError):
        service._validate_upload(
            UploadDocument("not-a-pdf.pdf", "application/pdf", b"not a pdf")
        )
    with pytest.raises(DocumentUploadValidationError):
        service._validate_upload(
            UploadDocument("not-an-image.png", "image/png", b"not a png")
        )
    with pytest.raises(DocumentUploadValidationError):
        service._validate_upload(
            UploadDocument(
                "large.png",
                "image/png",
                b"\x89PNG\r\n\x1a\n" + b"x" * (4 * 1024 * 1024),
            )
        )


@pytest.mark.integration
def test_document_upload_and_association_are_authenticated_and_isolated(tmp_path: Path):
    settings = Settings(
        document_storage_path=tmp_path,
        embedding_provider="gemini",
        gemini_api_key=None,
    )
    if settings.database_url is None:
        pytest.skip("DATABASE_URL is not configured")

    loop_factory = asyncio.SelectorEventLoop if sys.platform == "win32" else None
    with asyncio.Runner(loop_factory=loop_factory) as runner:
        runner.run(_exercise_document_api(settings, tmp_path))


async def _exercise_document_api(settings: Settings, storage_path: Path) -> None:
    application = create_app(settings)
    user_id = uuid4()
    model_id = uuid4()
    chatbot_a_id = uuid4()
    chatbot_b_id = uuid4()
    email = f"documents-{user_id}@bidachat.test"
    password = "valid document API password"

    async with application.router.lifespan_context(application):
        database = application.state.database
        try:
            async with database.session() as session:
                session.add_all(
                    [
                        User(
                            id=user_id,
                            email=email,
                            password_hash=hash_password(password),
                        ),
                        LlmModel(
                            id=model_id,
                            provider="test-provider",
                            model=f"document-model-{model_id}",
                        ),
                    ]
                )
                await session.flush()
                session.add_all(
                    [
                        Chatbot(
                            id=chatbot_a_id,
                            created_by=user_id,
                            configured_llm_model_id=model_id,
                            name="Document chatbot A",
                        ),
                        Chatbot(
                            id=chatbot_b_id,
                            created_by=user_id,
                            configured_llm_model_id=model_id,
                            name="Document chatbot B",
                        ),
                    ]
                )
                await session.commit()

            transport = ASGITransport(app=application)
            async with AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as client:
                upload_url = f"/api/v1/chatbots/{chatbot_a_id}/documents"
                unauthorized = await client.post(
                    upload_url,
                    files={"file": ("report.txt", b"private knowledge", "text/plain")},
                )
                assert unauthorized.status_code == 401

                login_response = await client.post(
                    "/api/v1/auth/login",
                    json={"email": email, "password": password},
                )
                headers = {
                    "Authorization": f"Bearer {login_response.json()['access_token']}"
                }

                rejected = await client.post(
                    upload_url,
                    headers=headers,
                    files={
                        "file": (
                            "invalid.exe",
                            b"not allowed",
                            "application/octet-stream",
                        )
                    },
                )
                assert rejected.status_code == 422
                assert list(storage_path.iterdir()) == []

                accepted = await client.post(
                    upload_url,
                    headers=headers,
                    files={"file": ("report.txt", b"private knowledge", "text/plain")},
                )
                assert accepted.status_code == 201
                uploaded = accepted.json()
                assert uploaded["chatbot_id"] == str(chatbot_a_id)
                assert uploaded["status"] == "failed"
                assert uploaded["error_code"] == "embedding_not_configured"
                assert uploaded["original_filename"] == "report.txt"
                assert len(list(storage_path.iterdir())) == 1

                retry_url = (
                    f"/api/v1/chatbots/{chatbot_a_id}/documents/"
                    f"{uploaded['id']}/processing"
                )
                assert (await client.post(retry_url)).status_code == 401
                wrong_chatbot_retry = await client.post(
                    f"/api/v1/chatbots/{chatbot_b_id}/documents/"
                    f"{uploaded['id']}/processing",
                    headers=headers,
                )
                assert wrong_chatbot_retry.status_code == 404
                retried = await client.post(retry_url, headers=headers)
                assert retried.status_code == 200
                assert retried.json()["error_code"] == "embedding_not_configured"
                assert len(list(storage_path.iterdir())) == 1

                oversized = await client.post(
                    upload_url,
                    headers=headers,
                    files={
                        "file": (
                            "too-large.txt",
                            b"x" * (20 * 1024 * 1024 + 1),
                            "text/plain",
                        )
                    },
                )
                assert oversized.status_code == 422
                assert len(list(storage_path.iterdir())) == 1

                chatbot_b_upload = await client.post(
                    f"/api/v1/chatbots/{chatbot_b_id}/documents",
                    headers=headers,
                    files={
                        "file": (
                            "other.pdf",
                            b"%PDF-1.7\nother knowledge",
                            "application/pdf",
                        )
                    },
                )
                assert chatbot_b_upload.status_code == 201

                listed = await client.get(upload_url, headers=headers)
                assert listed.status_code == 200
                assert [item["id"] for item in listed.json()] == [uploaded["id"]]

                association_url = f"{upload_url}/{uploaded['id']}"
                assert (await client.delete(association_url)).status_code == 401
                assert (
                    await client.delete(association_url, headers=headers)
                ).status_code == 204
                assert (await client.get(upload_url, headers=headers)).json() == []
                assert (
                    await client.delete(association_url, headers=headers)
                ).status_code == 404
                available = await client.get("/api/v1/documents", headers=headers)
                assert any(item["id"] == uploaded["id"] for item in available.json())
                reassociated = await client.post(
                    f"{upload_url}/associations",
                    headers=headers,
                    json={"document_ids": [uploaded["id"]]},
                )
                assert reassociated.status_code == 200
                assert [
                    item["id"]
                    for item in (await client.get(upload_url, headers=headers)).json()
                ] == [uploaded["id"]]
        finally:
            async with database.session() as session:
                await session.execute(
                    delete(Chatbot).where(Chatbot.created_by == user_id)
                )
                user = await session.get(User, user_id)
                if user is not None:
                    await session.delete(user)
                model = await session.get(LlmModel, model_id)
                if model is not None:
                    await session.delete(model)
                await session.commit()
            for stored_file in storage_path.glob("*") if storage_path.exists() else []:
                stored_file.unlink()
            storage_path.rmdir() if storage_path.exists() else None
