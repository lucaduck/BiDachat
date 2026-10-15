import os
import subprocess
from pathlib import Path


def test_failed_database_dump_restarts_backend_and_discards_partial_backup(
    tmp_path: Path,
):
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    (checkout / "docker-compose.production.yml").write_text("name: bidachat\n")
    (checkout / ".env").write_text("IMAGE_TAG=fixture\n")
    backups = tmp_path / "backups"
    binaries = tmp_path / "bin"
    binaries.mkdir()
    operations = tmp_path / "operations.log"
    docker = binaries / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'printf \'%s\\n\' "$*" >> "$OPERATIONS_LOG"\n'
        'case "$*" in\n'
        "  *'ps -a -q backend') printf 'backend-fixture\\n' ;;\n"
        "  'inspect -f {{.State.Running}} backend-fixture') printf 'true\\n' ;;\n"
        "  *'exec -T database sh -c '*'pg_dump'*) exit 27 ;;\n"
        "esac\n"
    )
    docker.chmod(0o755)
    script = Path(__file__).resolve().parents[2] / "docker/backup-production.sh"

    result = subprocess.run(
        ["sh", str(script)],
        cwd=checkout,
        env={
            **os.environ,
            "PATH": f"{binaries}:{os.environ['PATH']}",
            "BACKUP_DIR": str(backups),
            "OPERATIONS_LOG": str(operations),
        },
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    calls = operations.read_text()
    assert "stop backend" in calls
    assert "start backend" in calls
    assert list(backups.iterdir()) == []
