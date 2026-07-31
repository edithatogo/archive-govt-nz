"""Stable process exit states for automation."""

from enum import IntEnum


class ExitCode(IntEnum):
    """Documented non-overlapping archive outcomes."""

    SUCCESS = 0
    UNCHANGED = 10
    PARTIAL_SUCCESS = 20
    RESTRICTED = 30
    RETRYABLE_FAILURE = 40
    TERMINAL_FAILURE = 50
