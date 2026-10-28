"""Honor native Hub write cooldown proof before any new fenced mutation."""

from __future__ import annotations

import json
import math
import re
import subprocess
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, TypeGuard

from archive_govt_nz.parliament.hosted_transport import (
    MAX_RETRY_SECONDS,
    HostedError,
    abort,
)
lazy from archive_govt_nz.parliament.hosted import github_receipt, github_run

HISTORY_LIMIT = 100
MAX_LINKS = 8
CLOCK_SKEW = 120
RATE_LIMITED = 429
WRITE_REASONS = frozenset(
    {"checkpoint_commit_outcome_unknown", "publication_commit_outcome_unknown"}
)
OPERATIONS = frozenset(
    {"bootstrap", "verify", "pilot", "run", "hold", "pause", "resume", "enable"}
)
Reader = Callable[[str, str | None], dict[str, Any]]


def is_write_rate_limit(error: Exception) -> bool:
    """Recognize only explicit Hub mutation errors, never source access failures."""
    return (
        isinstance(error, HostedError)
        and error.http_status == RATE_LIMITED
        and str(error) in WRITE_REASONS
    )


def valid_delay(value: object) -> TypeGuard[int]:
    """Reject invented, malformed or unsupported reset windows."""
    return type(value) is int and 0 <= value <= MAX_RETRY_SECONDS


def deferred_failure(failure: dict[str, Any], now: float) -> dict[str, Any]:
    """Retain the first ambiguous write outcome without calling it archive success."""
    seconds = failure["retry_after_seconds"]
    if not valid_delay(seconds):
        abort("hub_write_cooldown_deadline_missing")
    return {
        "status": "deferred_hub_write",
        "operation": failure["operation"],
        "first_failure": dict(failure),
        "not_before": datetime.fromtimestamp(now + seconds, UTC).isoformat(),
        "source_acquisition_stopped": True,
        "checkpoint_reconciliation_required": True,
        "native_mutation_replayed": False,
        "coverage_claim": False,
        "recurrence_acceptance": False,
    }


def recent_runs() -> list[dict[str, Any]]:
    """Read bounded native history, including successful read-only deferrals."""
    result = subprocess.run(  # noqa: S603 - fixed read-only CLI endpoint
        [  # noqa: S607 - qualified existing CLI
            "gh",
            "api",
            "--method",
            "GET",
            "repos/edithatogo/archive-govt-nz/actions/workflows/parliament-continuation.yml/runs",
            "-f",
            "status=completed",
            "-f",
            f"per_page={HISTORY_LIMIT}",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    rows = json.loads(result.stdout)["workflow_runs"]
    if not isinstance(rows, list) or len(rows) > HISTORY_LIMIT:
        abort("hub_write_cooldown_history_bound")
    return rows


def _identity(run: object, attempt: object) -> tuple[str, str]:
    run, attempt = str(run), str(attempt)
    if not re.fullmatch(r"[0-9]{1,20}", run) or not re.fullmatch(
        r"[0-9]{1,10}", attempt
    ):
        abort("hub_write_cooldown_identity")
    return run, attempt


class _Proofs:
    """Resolve immutable origin receipts, not user-supplied deadline strings."""

    def __init__(self, get_run: Reader, get_receipt: Reader, now: float) -> None:
        self.get_run, self.get_receipt, self.now = get_run, get_receipt, now
        self.cache: dict[tuple[str, str], dict[str, Any] | None] = {}

    def deadline(
        self, key: tuple[str, str], seen: frozenset[tuple[str, str]] = frozenset()
    ) -> dict[str, Any] | None:
        if key in seen or len(seen) >= MAX_LINKS:
            abort("hub_write_cooldown_evidence_cycle")
        if key in self.cache:
            return self.cache[key]
        info = self.get_run(*key)
        if info["status"] != "completed":
            return None
        ended = datetime.fromisoformat(info["updated_at"])
        if ended.tzinfo is None or ended.timestamp() > self.now + CLOCK_SKEW:
            abort("hub_write_cooldown_clock")
        # No supported Retry-After can survive this conservative native age.
        if ended.timestamp() + MAX_RETRY_SECONDS <= self.now:
            return None
        try:
            receipt = self.get_receipt(*key)
        except HostedError as error:
            if str(error) != "native_receipt_missing":
                raise
            return None
        value = self._receipt(key, receipt, ended, seen | {key})
        self.cache[key] = value
        return value

    def _receipt(
        self,
        key: tuple[str, str],
        receipt: dict[str, Any],
        ended: datetime,
        seen: frozenset[tuple[str, str]],
    ) -> dict[str, Any] | None:
        failure = receipt.get("first_failure", receipt)
        if (
            isinstance(failure, dict)
            and failure.get("status") == "failed"
            and failure.get("operation") in OPERATIONS
            and failure.get("error_class") == "HostedError"
            and failure.get("reason") in WRITE_REASONS
            and failure.get("http_status") == RATE_LIMITED
        ):
            delay = failure.get("retry_after_seconds")
            if not valid_delay(delay):
                abort("hub_write_cooldown_deadline_missing")
            return {
                "cooldown_origin": {"run_id": key[0], "attempt": key[1]},
                "not_before_epoch": ended.timestamp() + delay,
            }
        if receipt.get("status") == "deferred_hub_write":
            origin = receipt.get("cooldown_origin", {})
            if set(origin) != {"run_id", "attempt"}:
                abort("hub_write_cooldown_evidence_unqualified")
            return self.deadline(_identity(origin["run_id"], origin["attempt"]), seen)
        return None


def find_cooldown(
    owner: str | None,
    history: list[dict[str, Any]],
    get_run: Reader,
    get_receipt: Reader,
    now: float,
) -> dict[str, Any] | None:
    """Return a no-write outcome while any qualified reset window is active."""
    if not math.isfinite(now) or len(history) > HISTORY_LIMIT:
        abort("hub_write_cooldown_history_bound")
    keys: list[tuple[str, str]] = []
    owned = re.fullmatch(r"gha_([0-9]{1,20})_([0-9]{1,10})", owner or "")
    if owned:
        keys.append((owned[1], owned[2]))
    keys.extend(
        _identity(row["id"], row["run_attempt"])
        for row in history
        if row["head_branch"] == "main"
        and row["event"] in {"schedule", "workflow_dispatch"}
    )
    proofs = _Proofs(get_run, get_receipt, now)
    for key in dict.fromkeys(keys):
        found = proofs.deadline(key)
        if found is not None and found["not_before_epoch"] > now:
            return {
                "status": "deferred_hub_write",
                "cooldown_origin": found["cooldown_origin"],
                "not_before": datetime.fromtimestamp(
                    found["not_before_epoch"], UTC
                ).isoformat(),
                "retry_after_seconds": math.ceil(found["not_before_epoch"] - now),
                "source_acquisition": False,
                "hf_control_mutation": False,
                "checkpoint_reconciliation_required": True,
                "coverage_claim": False,
                "recurrence_acceptance": False,
            }
    if len(history) == HISTORY_LIMIT and all(
        datetime.fromisoformat(row["updated_at"]).timestamp() + MAX_RETRY_SECONDS > now
        for row in history
    ):
        abort("hub_write_cooldown_history_incomplete")
    return None


def current_write_cooldown(owner: str | None) -> dict[str, Any] | None:
    """Use the existing qualified GitHub account and trusted workflow receipts."""
    return find_cooldown(owner, recent_runs(), github_run, github_receipt, time.time())
