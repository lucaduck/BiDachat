import os
import shutil
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _run(
    command: list[str],
    *,
    cwd: Path,
    environment: dict[str, str],
    input: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        input=input,
        text=True,
        capture_output=True,
        check=True,
    )


@pytest.mark.integration
def test_coordinated_backup_restores_records_and_originals(tmp_path: Path):
    if shutil.which("docker") is None:
        pytest.skip("Docker is unavailable")
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    backup_root = tmp_path / "backups"
    project = f"bidachat_backup_test_{uuid4().hex[:10]}"
    environment = {
        **os.environ,
        "COMPOSE_PROJECT_NAME": project,
        "BACKUP_DIR": str(backup_root),
    }
    (checkout / ".env").write_text("OLLAMA_ACCELERATION=cpu\nIMAGE_TAG=fixture\n")
    (checkout / "docker-compose.production.yml").write_text(
        "services:\n"
        "  database:\n"
        "    image: pgvector/pgvector:pg16\n"
        "    environment:\n"
        "      POSTGRES_USER: fixture\n"
        "      POSTGRES_PASSWORD: fixture-only\n"
        "      POSTGRES_DB: fixture\n"
        "      EMBEDDING_DIMENSIONS: '768'\n"
        "    tmpfs:\n"
        "      - /var/lib/postgresql/data:size=512m\n"
        "    volumes:\n"
        f"      - {ROOT / 'database/migrations'}:/migrations:ro\n"
        f"      - {ROOT / 'docker/postgres/init-database.sh'}:"
        "/docker-entrypoint-initdb.d/01-init-database.sh:ro\n"
        "    healthcheck:\n"
        "      test: ['CMD-SHELL', 'pg_isready -U fixture -d fixture']\n"
        "      interval: 2s\n"
        "      retries: 15\n"
        "  backend:\n"
        "    image: pgvector/pgvector:pg16\n"
        "    entrypoint: ['sh', '-c']\n"
        "    command: ['mkdir -p /app/storage/documents && exec sleep infinity']\n"
        "    volumes:\n"
        "      - originals:/app/storage/documents\n"
        "volumes:\n"
        "  originals:\n"
    )
    compose = ["docker", "compose", "-f", "docker-compose.production.yml"]
    try:
        _run([*compose, "up", "-d", "--wait"], cwd=checkout, environment=environment)
        _run(
            [
                *compose,
                "exec",
                "-T",
                "database",
                "psql",
                "-U",
                "fixture",
                "-d",
                "fixture",
                "-v",
                "ON_ERROR_STOP=1",
            ],
            cwd=checkout,
            environment=environment,
            input="""
                INSERT INTO users (id, email, password_hash)
                VALUES ('00000000-0000-0000-0000-000000000001',
                        'fixture@bidachat.test', 'fixture');
                INSERT INTO llm_models (id, provider, model)
                VALUES ('00000000-0000-0000-0000-000000000002', 'ollama', 'fixture');
                INSERT INTO chatbots (id, created_by, configured_llm_model_id, name)
                VALUES ('00000000-0000-0000-0000-000000000003',
                        '00000000-0000-0000-0000-000000000001',
                        '00000000-0000-0000-0000-000000000002', 'Fixture');
                INSERT INTO documents
                    (id, chatbot_id, original_filename, storage_key,
                     media_type, size_bytes)
                VALUES ('00000000-0000-0000-0000-000000000004',
                        '00000000-0000-0000-0000-000000000003',
                        'fixture.txt', 'documents/fixture.txt', 'text/plain', 7);
            """,
        )
        _run(
            [
                *compose,
                "exec",
                "-T",
                "backend",
                "sh",
                "-c",
                "printf 'fixture' > /app/storage/documents/fixture.txt",
            ],
            cwd=checkout,
            environment=environment,
        )
        backup = _run(
            ["sh", str(ROOT / "docker/backup-production.sh")],
            cwd=checkout,
            environment=environment,
        )
        bundle = Path(backup.stdout.strip().removeprefix("Verified backup: "))
        assert bundle.is_dir()
        assert (bundle / "manifest.sha256").is_file()
        assert _run(
            [*compose, "ps", "-q", "backend"], cwd=checkout, environment=environment
        ).stdout.strip()
        verified = _run(
            ["sh", str(ROOT / "docker/verify-production-backup.sh"), str(bundle)],
            cwd=checkout,
            environment=environment,
        )
        assert "Isolated restore passed" in verified.stdout
    finally:
        subprocess.run(
            [*compose, "down", "--volumes", "--remove-orphans"],
            cwd=checkout,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
