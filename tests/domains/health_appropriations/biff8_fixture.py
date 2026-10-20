"""Fictional real-reader BIFF8 in a small, single-FAT CFB container."""

from __future__ import annotations

import struct

_BLOCK = 512
_MIN_STREAM = 4096
_FAT_ENTRIES = 128
_END = -2
_FREE = -1
_FAT = -3


def record(kind: int, payload: bytes = b"") -> bytes:
    return struct.pack("<HH", kind, len(payload)) + payload


def bof(kind: int) -> bytes:
    return record(0x0809, struct.pack("<HHHHII", 0x0600, kind, 0x0DBB, 1997, 0x41, 6))


def compound(stream: bytes, *, declared_size: int | None = None) -> bytes:
    sectors = max(_MIN_STREAM, (len(stream) + _BLOCK - 1) // _BLOCK * _BLOCK) // _BLOCK
    assert sectors + 2 <= _FAT_ENTRIES, "fixture deliberately has one FAT sector"
    stream = stream.ljust(sectors * _BLOCK, b"\0")
    header = bytearray(_BLOCK)
    header[:8] = bytes.fromhex("d0cf11e0a1b11ae1")
    struct.pack_into("<HHHHH", header, 24, 0x003E, 3, 0xFFFE, 9, 6)
    struct.pack_into("<III", header, 40, 0, 1, sectors)
    struct.pack_into("<I", header, 56, _MIN_STREAM)
    struct.pack_into("<iIiI", header, 60, _END, 0, _END, 0)
    struct.pack_into("<109i", header, 76, sectors + 1, *([_FREE] * 108))

    def entry(name: str, kind: int, child: int, first: int, size: int) -> bytes:
        data = bytearray(128)
        title = (name + "\0").encode("utf-16le")
        data[: len(title)] = title
        struct.pack_into("<HBBiii", data, 64, len(title), kind, 1, _FREE, _FREE, child)
        struct.pack_into("<iQ", data, 116, first, size)
        return bytes(data)

    size = len(stream) if declared_size is None else declared_size
    directory = (
        entry("Root Entry", 5, 1, _END, 0)
        + entry("Workbook", 2, _FREE, 0, size)
        + bytes(256)
    )
    fat = [_FREE] * _FAT_ENTRIES
    for index in range(sectors - 1):
        fat[index] = index + 1
    fat[sectors - 1] = _END
    fat[sectors] = _END
    fat[sectors + 1] = _FAT
    return bytes(header) + stream + directory + struct.pack("<128i", *fat)


def numeric_fixture(*, failure: str | None = None) -> bytes:
    def bound(offset: int, name: bytes, kind: int = 0) -> bytes:
        return record(
            0x0085, struct.pack("<IBBBB", offset, 0, kind, len(name), 0) + name
        )

    def number(row: int, value: float) -> bytes:
        return record(0x0203, struct.pack("<HHHd", row, 0, 0, value))

    eof = record(0x000A)
    start = bof(5) + record(0x0042, struct.pack("<H", 1200)) + record(0x00E0, bytes(20))
    if failure == "encryption":
        start += record(0x002F, bytes(6))
    first = len(start) + len(bound(0, b"Raw Data")) + len(bound(0, b"Other")) + len(eof)
    text = "Fictional Māori"
    label = record(
        0x0204, struct.pack("<HHHHB", 0, 0, 0, len(text), 1) + text.encode("utf-16le")
    )
    high = int.from_bytes(struct.pack("<d", 42.0)[4:], "little")
    signed = ((-7 << 2) & 0xFFFFFFFF) | 2
    tokens = bytes([0x1E, 1, 0, 0x1E, 1, 0, 0x03])
    sheet = (
        bof(0x10)
        + record(0x0081, struct.pack("<H", 0x0010 if failure == "dialog" else 0x04C1))
        + record(0x0200, struct.pack("<IIHHH", 0, 6, 0, 2, 0))
        + label
        + number(1, 42.0)
        + record(0x027E, struct.pack("<HHHI", 2, 0, 0, high))
        + record(0x027E, struct.pack("<HHHI", 3, 0, 0, signed))
        + record(
            0x00BD,
            struct.pack("<HHHIHIH", 4, 0, 0, (12300 << 2) | 3, 0, (123 << 2) | 3, 1),
        )
        + record(
            0x0006, struct.pack("<HHHdHIH", 5, 0, 0, 2.0, 0, 0, len(tokens)) + tokens
        )
    )
    if failure == "duplicate_cell":
        sheet += number(1, 42.0)
    if failure == "malformed_number":
        sheet += record(0x0203, bytes(13))
    sheet += eof
    other = bof(0x10) + record(0x0081, bytes(2)) + eof
    second_name = b"Raw Data" if failure == "duplicate_names" else b"Other"
    # Name lengths affect the first BOF position as well as their pointers.
    first = (
        len(start) + len(bound(0, b"Raw Data")) + len(bound(0, second_name)) + len(eof)
    )
    second = first if failure == "duplicate_offsets" else first + len(sheet)
    kind = 1 if failure == "macro" else 0
    stream = (
        start
        + bound(first, b"Raw Data", kind)
        + bound(second, second_name)
        + eof
        + sheet
        + other
    )
    size = 2**32 + _MIN_STREAM if failure == "high_stream_size" else None
    return compound(stream, declared_size=size)


def grid_fixture(
    sheets: tuple[tuple[str, tuple[tuple[object, ...], ...]], ...],
) -> bytes:
    """Encode fictional label/NUMBER cells in real BIFF8 worksheets."""
    eof = record(0x000A)
    start = bof(5) + record(0x0042, struct.pack("<H", 1200)) + record(0x00E0, bytes(20))

    def bound(offset: int, name: str) -> bytes:
        return record(
            0x0085,
            struct.pack("<IBBBB", offset, 0, 0, len(name), 1) + name.encode("utf-16le"),
        )

    bodies = []
    for _, rows in sheets:
        body = bof(0x10) + record(0x0081, struct.pack("<H", 0x04C1))
        body += record(
            0x0200,
            struct.pack("<IIHHH", 0, len(rows), 0, max(map(len, rows), default=0), 0),
        )
        for row, cells in enumerate(rows):
            for col, value in enumerate(cells):
                if value is None:
                    continue
                if isinstance(value, str):
                    body += record(
                        0x0204,
                        struct.pack("<HHHHB", row, col, 0, len(value), 1)
                        + value.encode("utf-16le"),
                    )
                else:
                    assert type(value) in {int, float}
                    body += record(0x0203, struct.pack("<HHHd", row, col, 0, value))
        bodies.append(body + eof)
    offset = len(start) + sum(len(bound(0, name)) for name, _ in sheets) + len(eof)
    pointers = []
    for (name, _), body in zip(sheets, bodies, strict=True):
        pointers.append(bound(offset, name))
        offset += len(body)
    return compound(start + b"".join(pointers) + eof + b"".join(bodies))
