"""Reserve operation Gold output without redirecting writes through replaced paths."""

from __future__ import annotations

import ctypes
import os
import stat
from contextlib import ExitStack, contextmanager
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


def _require(condition: object) -> None:
    if not condition:
        message = "operation_context_gold_invalid"
        raise ValueError(message)


def _identity(status: os.stat_result) -> tuple[int, int]:
    _require(stat.S_ISDIR(status.st_mode))
    _require(not getattr(status, "st_file_attributes", 0) & 0x400)
    return status.st_dev, status.st_ino


def _lock_windows_directory(path: Path, stack: ExitStack) -> None:
    """Deny write/delete handles, including reparse changes, until readback ends."""

    class FileIdInfo(ctypes.Structure):
        _fields_ = [
            ("volume", ctypes.c_ulonglong),
            ("identifier", ctypes.c_ubyte * 16),
        ]

    class AttributeTagInfo(ctypes.Structure):
        _fields_ = [("attributes", wintypes.DWORD), ("tag", wintypes.DWORD)]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create.restype = wintypes.HANDLE
    information = kernel.GetFileInformationByHandleEx
    information.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    information.restype = wintypes.BOOL
    close = kernel.CloseHandle
    close.argtypes = [wintypes.HANDLE]
    close.restype = wintypes.BOOL
    before = path.lstat()
    _identity(before)
    # FILE_LIST_DIRECTORY | FILE_READ_ATTRIBUTES: attribute-only opens do not
    # participate in data-access sharing checks. FILE_SHARE_READ; OPEN_EXISTING;
    # BACKUP_SEMANTICS (directory) | OPEN_REPARSE_POINT (never follow a junction).
    handle = create(str(path), 0x81, 1, None, 3, 0x02000000 | 0x00200000, None)
    if handle in (None, ctypes.c_void_p(-1).value):
        raise ctypes.WinError(ctypes.get_last_error())
    stack.callback(close, handle)
    identity = FileIdInfo()
    attributes = AttributeTagInfo()
    if not information(handle, 18, ctypes.byref(identity), ctypes.sizeof(identity)):
        raise ctypes.WinError(ctypes.get_last_error())
    if not information(handle, 9, ctypes.byref(attributes), ctypes.sizeof(attributes)):
        raise ctypes.WinError(ctypes.get_last_error())
    _require(attributes.attributes & 0x10 and not attributes.attributes & 0x400)
    _require(int.from_bytes(bytes(identity.identifier), "little") == before.st_ino)
    _require(_identity(path.lstat()) == _identity(before))


@dataclass(frozen=True)
class ReservedGoldDirectory:
    """Writer bound to one exclusively reserved directory's lifetime."""

    path: Path
    identity: tuple[int, int]
    descriptor: int | None

    def guard(self) -> None:
        """Reject substitution of the reserved directory identity."""
        _require(not self.path.is_symlink())
        _require(_identity(self.path.lstat()) == self.identity)

    def write(self, name: str, payload: bytes) -> None:
        """Create one trusted portable member exclusively, then check identity."""
        _require(name not in {"", ".", ".."} and not any(c in name for c in "/\\:"))
        self.guard()
        if os.name == "nt":
            _require(self.descriptor is None)
            # Every Windows ancestor and the leaf are held against write/delete
            # opens; this is never an unlocked descriptorless fallback.
            stream = (self.path / name).open("xb")
        else:
            _require(self.descriptor is not None)
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
            descriptor = os.open(name, flags, 0o600, dir_fd=self.descriptor)
            try:
                stream = os.fdopen(descriptor, "wb")
            except BaseException:
                os.close(descriptor)
                raise
        with stream:
            _require(stream.write(payload) == len(payload))
        self.guard()


@contextmanager
def reserve_gold_directory(path: Path) -> Iterator[ReservedGoldDirectory]:
    """Keep all protective handles alive through writes and final readback."""
    path.mkdir()
    identity = _identity(path.lstat())
    with ExitStack() as stack:
        descriptor = None
        if os.name == "nt":
            # Normalize lexical components without following substituted links.
            absolute = Path(os.path.abspath(path))  # noqa: PTH100
            for ancestor in (*reversed(absolute.parents), absolute):
                _lock_windows_directory(ancestor, stack)
        else:
            descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            stack.callback(os.close, descriptor)
            _require(_identity(os.fstat(descriptor)) == identity)
        directory = ReservedGoldDirectory(path, identity, descriptor)
        directory.guard()
        yield directory
        directory.guard()
