import base64
import json
import os
import struct
import zlib

import httpx

client = httpx.Client(base_url="http://localhost:8000/api/v1", timeout=900)
created = []


def call(method, path, **kwargs):
    response = client.request(method, path, **kwargs)
    if response.status_code >= 400:
        raise RuntimeError(f"{method} {path}: HTTP {response.status_code}")
    return response.json() if response.content else None


try:
    login = call(
        "POST",
        "/auth/login",
        json={
            "email": os.environ["ADMIN_EMAIL"],
            "password": os.environ["ADMIN_PASSWORD"],
        },
    )
    client.headers["Authorization"] = "Bearer " + login["access_token"]
    settings = call("GET", "/settings")
    assert settings["embedding_provider"] == "ollama"
    model = next(m for m in call("GET", "/llm-models") if m["model"] == "qwen3-vl:2b")
    for label in ("A", "B"):
        bot = call(
            "POST",
            "/chatbots",
            json={
                "name": f"Local integration check {label}",
                "configured_llm_model_id": model["id"],
                "behavior_instructions": (
                    "Responde en español y brevemente. "
                    "Usa los documentos proporcionados cuando correspondan."
                ),
            },
        )
        created.append(bot["id"])
    bot_id = created[0]
    doc = call(
        "POST",
        f"/chatbots/{bot_id}/documents",
        files={
            "file": (
                "test.txt",
                b"El indicador Faro tiene un valor de 137 unidades en septiembre.",
                "text/plain",
            )
        },
    )
    assert doc["status"] == "ready", doc["status"]
    print("Document upload and local embedding: ready", flush=True)
    import asyncio
    from uuid import UUID

    from app.core.config import get_settings
    from app.database.session import Database
    from app.llm.provider import LlmProvider
    from app.services.rag_knowledge_service import RagKnowledgeService

    async def check_isolation():
        config = get_settings()
        database = Database.from_settings(config)
        try:
            vector = await LlmProvider(config).embed(
                "indicador Faro", task_type="RETRIEVAL_QUERY"
            )
            async with database.session() as session:
                results = []
                for bid in created:
                    results.append(
                        await RagKnowledgeService(config).retrieve_chunks(
                            session,
                            chatbot_id=UUID(bid),
                            embedding_model=config.embedding_model,
                            embedding_dimensions=config.embedding_dimensions,
                            query_embedding=vector,
                        )
                    )
                assert any("137" in c.content for c in results[0])
                assert results[1] == []
        finally:
            await database.dispose()

    asyncio.run(check_isolation())
    print("Actual pgvector retrieval isolation: passed", flush=True)
    answer = call(
        "POST",
        f"/chatbots/{bot_id}/queries",
        json={"question": "¿Cuál es el valor del indicador Faro en septiembre?"},
    )
    print("RAG:", json.dumps(answer, ensure_ascii=False), flush=True)
    assert "137" in answer["answer"]
    width, height = 256, 256
    rows = []
    for y in range(height):
        row = bytearray()
        for x in range(width):
            color = (255, 255, 255)
            if 35 <= x < 95 and 130 <= y < 225:
                color = (0, 70, 240)
            if 155 <= x < 215 and 35 <= y < 225:
                color = (235, 20, 30)
            row.extend(color)
        rows.append(b"\0" + row)

    def chunk(tag, data):
        return (
            struct.pack("!I", len(data))
            + tag
            + data
            + struct.pack("!I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack("!2I5B", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"".join(rows)))
        + chunk(b"IEND", b"")
    )
    answer = call(
        "POST",
        f"/chatbots/{bot_id}/queries",
        json={
            "question": "Observa la imagen. ¿Qué color tiene la barra más alta?",
            "image_base64": base64.b64encode(png).decode(),
            "image_mime_type": "image/png",
        },
    )
    print("Vision:", json.dumps(answer, ensure_ascii=False), flush=True)
    assert "roj" in answer["answer"].lower()
    metrics = call("GET", f"/chatbots/{bot_id}/metrics")
    assert metrics["completed_queries"] == 2 and metrics["failed_queries"] == 0
    print("Metrics:", json.dumps(metrics), flush=True)
finally:
    for bot_id in created:
        call("DELETE", f"/chatbots/{bot_id}")
    if "Authorization" in client.headers:
        call("POST", "/auth/logout")
    client.close()
