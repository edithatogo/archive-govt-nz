"""Non-interactive trusted-main Parliament workflow and operator entrypoint."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import mkstemp
from typing import TYPE_CHECKING

from archive_govt_nz.parliament.hosted import (
    bootstrap,
    install_signals,
    run,
    validate_enable_proofs,
)
from archive_govt_nz.parliament.hosted_checkpoint import Checkpoints
from archive_govt_nz.parliament.hosted_state import digest
from archive_govt_nz.parliament.hosted_transport import (
    HostedError,
    NativeTransport,
    abort,
)

if TYPE_CHECKING:
    from collections.abc import Iterator


def control(args: argparse.Namespace, transport: NativeTransport) -> dict[str, object]:
    """Pause safely or enable only after exact native acceptance proof."""
    manager = Checkpoints(transport, args.state_dir)
    manager.load()
    if args.operation in {"enable", "resume"}:
        if args.operation == "enable":
            validate_enable_proofs(
                args.pilot_run, args.cancelled_run, args.restored_run
            )
        if (
            manager.pointer["owner"]
            or manager.pointer["checkpoint"] is None
            or manager.pointer["checkpoint"]["status"] != "verified"
        ):
            abort("handover_not_quiescent")
        if (
            digest(transport.read("README.md", manager.parent))
            != manager.pointer["card_sha256"]
        ):
            abort("maintained_card_changed")
        if args.operation == "enable":
            manager.pointer.update(authority="hosted", enabled=True)
        # Resume is an explicit operator action after review. It preserves the
        # existing enable/authority state and cannot bypass initial acceptance.
        manager.pointer.update(paused=None)
    else:
        manager.pointer.update(enabled=False, paused="operator")
    manager.write_pointer()
    return {
        "status": args.operation,
        "checkpoint": manager.pointer["checkpoint"],
    }


@contextmanager
def private_diagnostics(root: Path) -> Iterator[None]:
    """Keep direct SDK stdout/stderr inside private, spool-accounted files."""
    root.mkdir(parents=True, exist_ok=True)
    descriptor, _path = mkstemp(prefix=".private-sdk-", suffix=".log", dir=root)
    with (
        os.fdopen(descriptor, "w", encoding="utf-8", errors="backslashreplace") as log,
        redirect_stdout(log),
        redirect_stderr(log),
    ):
        yield


def execute(args: argparse.Namespace) -> dict[str, object]:
    """Perform one selected operation inside the private diagnostic boundary."""
    transport = NativeTransport()
    if args.operation == "bootstrap":
        if args.index is None:
            abort("bootstrap_index_required")
        return bootstrap(args.state_dir, args.index, transport)
    if args.operation in {"pause", "resume", "enable"}:
        return control(args, transport)
    return run(
        args.state_dir,
        mode=args.operation,
        max_batches=args.max_batches,
        max_seconds=args.max_seconds,
        hold_seconds=args.hold_seconds,
    )


def main() -> int:
    """Write only a sanitized control receipt; never upload SDK logs or spool."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation",
        choices=["bootstrap", "verify", "pilot", "run", "pause", "resume", "enable"],
    )
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--index", type=Path)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--max-batches", type=int, default=1)
    parser.add_argument("--max-seconds", type=int, default=10800)
    parser.add_argument("--hold-seconds", type=int, default=0)
    parser.add_argument("--pilot-run")
    parser.add_argument("--cancelled-run")
    parser.add_argument("--restored-run")
    args = parser.parse_args()
    logging.disable(logging.CRITICAL)
    install_signals()
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(
        json.dumps({"status": "started", "operation": args.operation})
    )
    code = 0
    try:
        with private_diagnostics(args.state_dir):
            result = execute(args)
    except KeyboardInterrupt:
        result = {"status": "interrupted", "operation": args.operation}
        code = 130
    except Exception as error:  # noqa: BLE001 - CLI writes sanitized failure receipt
        result = {
            "status": "failed",
            "operation": args.operation,
            "error_class": type(error).__name__,
        }
        if isinstance(error, HostedError):
            result["reason"] = str(error)
        code = 1
    args.receipt.write_text(json.dumps(result, indent=2))
    sys.stdout.write(json.dumps(result) + "\n")
    return code
