"""Reconcile Hansard volume labels against numbered catalogue items."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

NUMBER = re.compile(r"\bv\.\s*(\d{1,3})\b", re.IGNORECASE)
PERIOD = re.compile(
    r"([A-Z]{3,9})\.?\s*(\d{1,2})?\s*[- ]\s*"
    r"(?:([A-Z]{3,9})\.?\s*)?(\d{1,2})?\s+(19\d\d)"
)
CATALOGUE_PERIOD = re.compile(
    r"v\.(\d+) mo\.([A-Z]{3})(\d\d)-([A-Z]{3})(\d\d) yr\.(\d{4})"
)


def numbered_period(label: str) -> tuple[str, ...] | None:
    """Read both numeric-day conventions used by copies in the union catalogue."""
    compact = CATALOGUE_PERIOD.fullmatch(label)
    if compact:
        return compact.groups()
    alternate = re.fullmatch(
        r"v\.(\d+) (\d{4}):([A-Za-z]+)[.-]?(\d+)-([A-Za-z]+)\.?(\d+)", label
    )
    if alternate:
        volume, year, first_month, first_day, last_month, last_day = alternate.groups()
        return (
            volume,
            first_month[:3].upper(),
            first_day,
            last_month[:3].upper(),
            last_day,
            year,
        )
    return None


def reconcile(label: str, items: list[dict]) -> tuple[int | None, str, list[str]]:
    """Accept explicit volume labels or uniquely supported calendar bounds."""
    if match := NUMBER.search(label):
        return int(match[1]), "explicit_volume_label", []
    if re.fullmatch(r"[1-9]\d{0,2}", label):
        return int(label), "numeric_enumeration", []
    period = PERIOD.fullmatch(label)
    candidates: dict[int, list[str]] = {}
    if period:
        start, first_day, end, last_day, year = period.groups()
        for item in items:
            match = numbered_period(item.get("enumcron") or "")
            if match is None:
                continue
            volume, first_month, first, last_month, last, item_year = match
            if (year, start[:3], (end or start)[:3]) != (
                item_year,
                first_month,
                last_month,
            ):
                continue
            if first_day and int(first_day) != int(first):
                continue
            if last_day and int(last_day) != int(last):
                continue
            candidates.setdefault(int(volume), []).append(item["htid"])
    if len(candidates) == 1:
        volume, witnesses = next(iter(candidates.items()))
        return volume, "catalogue_period_match", witnesses
    return None, "unresolved", []


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("inventory", "catalogue", "output"):
        parser.add_argument(argument, type=Path)
    args = parser.parse_args()
    seed = json.loads(args.inventory.read_bytes())["volumes"]
    items = json.loads(args.catalogue.read_bytes())["items"]
    rows = []
    for row in seed:
        number = row["volume_number"]
        basis, witnesses = "existing_inventory", []
        if number is None:
            number, basis, witnesses = reconcile(row["enumeration"], items)
        rows.append(
            {
                "htid": row["htid"],
                "label": row["enumeration"],
                "volume": number,
                "basis": basis,
                "witness_htids": witnesses,
            }
        )
    with args.output.open("x", encoding="utf-8") as out:
        json.dump(rows, out, indent=2)
