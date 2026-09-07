"""Real process termination must release ownership, not erase capture evidence."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest
from tests.domains.health_appropriations.test_capture_checkpoint import setup

_DRIVER = """
import argparse, asyncio, runpy, sys
from pathlib import Path
from archive_govt_nz.capture import CaptureResult
from archive_govt_nz.warc import write_response_record
execute = runpy.run_path(sys.argv[1])["_capture"]
root = Path(sys.argv[2])
args = argparse.Namespace(census=root/"census.json", store_root=root/"cas",
    warc_dir=root/"warcs", manifest=root/"manifest.json",
    max_resource_bytes=1024, resume=False)
async def local(client, url, store, config, *, transaction_warc_path):
    if url.endswith("two.csv"):
        sys.stdout.buffer.write(b"checkpoint_ready\\n")
        sys.stdout.buffer.flush()
        await asyncio.Event().wait()
    payload = b"synthetic"
    receipt = store.put_bytes(payload)
    warc = write_response_record(transaction_warc_path, url=url,
        status_code=200, headers={"content-type": "text/csv"}, body=payload)
    return CaptureResult(url, 200, "text/csv", receipt, warc)
execute.__globals__["capture_url"] = local
asyncio.run(execute(args))
"""


@pytest.mark.anyio
async def test_hard_kill_releases_writer_and_resumes_verified_checkpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Kill an actual writer after checkpoint; retain WARC and skip its request."""
    execute, args, calls = setup(tmp_path, monkeypatch)
    census = json.loads(args.census.read_text())
    census["records"].append(
        dict(
            census["records"][0],
            source_id="two",
            url="https://www.treasury.govt.nz/two.csv",
        )
    )
    args.census.write_text(json.dumps(census))
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-c",
        _DRIVER,
        str(Path(__file__).parents[3] / "tools/capture_health_resources.py"),
        str(tmp_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        assert process.stdout is not None
        assert (
            await asyncio.wait_for(process.stdout.readline(), 10)
            == b"checkpoint_ready\n"
        )
        checkpoint = json.loads(args.manifest.read_text())
        first = checkpoint["results"][0]
        lock = args.manifest.with_name(args.manifest.name + ".lock")
        lock_identity = lock.stat().st_ino
        warc = args.warc_dir / first["warc_path"]
        original = warc.read_bytes()
        args.resume = True
        # An active owner cannot be displaced, even by an explicit resume.
        with pytest.raises((OSError, ValueError)):
            await execute(args)
        assert not calls
        process.kill()
        await asyncio.wait_for(process.wait(), 10)
        assert process.returncode != 0
        result = await execute(args)
        assert calls == ["https://www.treasury.govt.nz/two.csv"]
        assert result["results"][0] == first
        assert result["captured"] == 2
        assert warc.read_bytes() == original
        assert await execute(args) == result
        assert len(calls) == 1
        assert lock.is_file()
        assert lock.stat().st_ino == lock_identity
    finally:
        if process.returncode is None:
            process.kill()
        await asyncio.wait_for(process.communicate(), 10)
