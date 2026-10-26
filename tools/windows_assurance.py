"""Run the complete Windows gate with a bounded, independently saved log."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path, PureWindowsPath

GATE_TIMEOUT_SECONDS = 2700


def run_logged_gate(
    command: tuple[str, ...], log: Path, *, timeout: float = GATE_TIMEOUT_SECONDS
) -> int:
    """Keep descendants off runner pipes and retain output even after a stall."""
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("wb") as output:
        process = subprocess.Popen(  # noqa: S603 - fixed internal gate, no shell
            command,
            stdout=output,
            stderr=subprocess.STDOUT,
            start_new_session=os.name == "posix",
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        started = time.monotonic()
        offset = 0
        with log.open("rb") as reader:
            while process.poll() is None:
                reader.seek(offset)
                chunk = reader.read(65536)
                offset += len(chunk)
                if chunk:
                    print(chunk.decode("utf-8", errors="replace"), end="", flush=True)
                if time.monotonic() - started >= timeout:
                    print("Windows aggregate gate deadline exceeded", flush=True)
                    try:
                        if os.name == "posix":
                            os.killpg(process.pid, signal.SIGKILL)
                        else:
                            subprocess.run(  # noqa: S603 - absolute system taskkill
                                (
                                    str(
                                        PureWindowsPath(
                                            os.environ.get("SYSTEMROOT", r"C:\Windows")
                                        )
                                        / "System32"
                                        / "taskkill.exe"
                                    ),
                                    "/PID",
                                    str(process.pid),
                                    "/T",
                                    "/F",
                                ),
                                check=False,
                                timeout=30,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.STDOUT,
                            )
                    finally:
                        process.kill()
                        process.wait(timeout=10)
                    return 124
                time.sleep(min(1, timeout / 10))
            reader.seek(offset)
            print(reader.read().decode("utf-8", errors="replace"), end="", flush=True)
        return process.returncode


def main() -> int:
    """Use the selected interpreter and every unchanged locked gate stage."""
    return run_logged_gate(
        (
            sys.executable,
            "-u",
            "tools/check.py",
            "--pytest-workers",
            "auto",
            "--pytest-distribution",
            "worksteal",
            "--pytest-diagnostics",
        ),
        Path("build/assurance.log"),
    )


if __name__ == "__main__":
    raise SystemExit(main())
