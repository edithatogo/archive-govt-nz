"""Process-lifetime local writer fencing that releases on process termination."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import BinaryIO


def file_lock(handle: BinaryIO, *, release: bool = False) -> None:
    """Use the platform's nonblocking lock without deleting its shared inode."""
    handle.seek(0)
    if sys.platform == "win32":
        import msvcrt  # noqa: PLC0415 - platform-specific standard library

        mode = msvcrt.LK_UNLCK if release else msvcrt.LK_NBLCK
        msvcrt.locking(handle.fileno(), mode, 1)
    else:
        import fcntl  # noqa: PLC0415 - platform-specific standard library

        mode = fcntl.LOCK_UN if release else fcntl.LOCK_EX | fcntl.LOCK_NB
        fcntl.flock(handle.fileno(), mode)
