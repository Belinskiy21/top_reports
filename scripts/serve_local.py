import socket
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"


def main() -> int:
    python = str(PYTHON if PYTHON.exists() else "python3")

    if not _port_is_available("127.0.0.1", 8000):
        print(
            (
                "Local startup failed because port 8000 is already in use.\n"
                "Stop the existing process on port 8000 or use a different port, then retry."
            ),
            file=sys.stderr,
        )
        return 1

    if not _run_step(
        [python, "-m", "db.seed"],
        failure_message=(
            "Local startup failed while seeding the database.\n"
            "PostgreSQL is not reachable on the configured host/port.\n"
            "Start PostgreSQL locally or run `docker compose up -d db redis`, then retry."
        ),
    ):
        return 1

    print("Starting startup prefetch in background...", flush=True)
    _ = subprocess.Popen(
        [python, "-m", "app.bootstrap_prefetch"],
        cwd=PROJECT_ROOT,
    )

    return subprocess.call(
        [python, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=PROJECT_ROOT,
    )


def _run_step(command: list[str], *, failure_message: str) -> bool:
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0:
        if completed.stdout:
            print(completed.stdout, end="")
        if completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)
        return True

    print("", file=sys.stderr)
    print(failure_message, file=sys.stderr)
    return False


def _port_is_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock.connect_ex((host, port)) != 0


if __name__ == "__main__":
    raise SystemExit(main())
