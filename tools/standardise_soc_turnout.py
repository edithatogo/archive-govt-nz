"""Direct age standardisation of retained 2023 registered-elector turnout.

These are descriptive compositional adjustments, not causal effects or forecasts.
The two explicit standards are drawn from the same retained turnout workbook;
Census residents are never substituted for registered-elector denominators.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

ORIGINAL_SHA = "ecf32160d7aa7a024861bd402877f2eacd11a1a5308eac385f2948447c1a78be"
NORMALISED_SHA = "2a257681b105e542e568340d0a64120cc1ed56113bd0ae891bcfd3639c24b2bc"
AGES = ("18 - 24", "25 - 29", "30 - 34", "35 - 39", "40 - 44", "45 - 49",
        "50 - 54", "55 - 59", "60 - 64", "65 - 69", "70+")
TOTALS = {"voters": 2_858_896, "nonvoters": 829_396, "enrolled": 3_688_292}


def require(condition: bool, message: str) -> None:
    """Reject an incompatible input with a bounded diagnostic."""
    if not condition:
        raise ValueError(message)


def load_rows(path: Path) -> list[dict[str, Any]]:
    """Independently bind the complete normalised input before interpreting rows."""
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == NORMALISED_SHA, "input digest mismatch")
    rows = json.loads(raw)
    require(isinstance(rows, list), "invalid input rows")
    return rows


def _label(code: int) -> str:
    return "general_electorate" if code < 66 else "maori_electorate"


def _percent(numerator: int, denominator: int) -> Decimal:
    return Decimal(numerator) * 100 / denominator


def _render(value: Decimal) -> str:
    """Retain precision beyond displayed percentage-point changes."""
    return format(value.quantize(Decimal("0.000000000001")), "f")


def standardise(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Apply national and within-roll age standards without pooling Census areas."""
    groups: dict[int, dict[str, dict[str, Any]]] = defaultdict(dict)
    identities: dict[int, str] = {}
    for row in rows:
        require(row.get("synthetic") is False and row.get("source_sha256") == ORIGINAL_SHA,
                "turnout source identity mismatch")
        require(row.get("boundary_vintage") == "2020" and row.get("election_year") == 2023,
                "wrong electoral vintage")
        code, name, age = row.get("electorate_number"), row.get("geography_name"), row.get("age_band")
        require(type(code) is int and 1 <= code <= 72 and isinstance(name, str) and bool(name),
                "invalid electorate identity")
        require(code not in identities or identities[code] == name, "electorate identity drift")
        identities[code] = name
        require(age in AGES, "unknown age stratum")
        require(age not in groups[code], "duplicate age stratum")
        require(all(type(row.get(k)) is int and row[k] >= 0 for k in TOTALS),
                "invalid turnout counts")
        require(row["enrolled"] > 0, "nonpositive age denominator")
        require(row["voters"] + row["nonvoters"] == row["enrolled"], "count conservation failed")
        groups[code][age] = row
    require(set(groups) == set(range(1, 73)) and all(set(group) == set(AGES) for group in groups.values()),
            "incomplete electorate/age strata")
    require(len(set(identities.values())) == 72, "duplicate electorate identity")
    require({k: sum(r[k] for r in rows) for k in TOTALS} == TOTALS,
            "national count reconciliation failed")

    references: dict[str, dict[str, int]] = {key: dict.fromkeys(AGES, 0) for key in
                                          ("national", "general_electorate", "maori_electorate")}
    for row in rows:
        references["national"][row["age_band"]] += row["enrolled"]
        references[_label(row["electorate_number"])][row["age_band"]] += row["enrolled"]
    result = []
    with localcontext() as context:
        context.prec = 50
        for code, strata in sorted(groups.items()):
            system = _label(code)
            voters = sum(r["voters"] for r in strata.values())
            enrolled = sum(r["enrolled"] for r in strata.values())
            raw_rate = _percent(voters, enrolled)
            for standard, ref_key in (("national_enrolled_2023", "national"),
                                      ("same_roll_system_enrolled_2023", system)):
                reference = references[ref_key]
                reference_total = sum(reference.values())
                adjusted = sum((Decimal(reference[age]) / reference_total
                                * Decimal(strata[age]["voters"]) / strata[age]["enrolled"]
                                for age in AGES), Decimal(0)) * 100
                require(0 <= adjusted <= 100, "standardised percentage outside bounds")
                result.append({
                    "electorate_number": code, "geography_name": identities[code],
                    "geography_system": system, "boundary_vintage": "2020", "election_year": 2023,
                    "standard": standard, "standard_reference_group": ref_key,
                    "standard_reference_enrolled": reference_total, "age_strata": len(AGES),
                    "voters": voters, "enrolled": enrolled,
                    "raw_turnout_percent": _render(raw_rate),
                    "standardised_turnout_percent": _render(adjusted),
                    "adjustment_percentage_points": _render(adjusted - raw_rate),
                    "population": "registered_electors_at_election_day_roll_closure",
                    "source_sha256": ORIGINAL_SHA, "normalised_input_sha256": NORMALISED_SHA,
                    "method": "direct_age_standardisation_of_age_specific_registered_elector_turnout",
                    "synthetic": False, "causal_claim": False,
                })
    receipt = {
        "schema_version": "soc-turnout-age-standardisation-v1",
        "electorates": len(groups), "rows": len(result), "age_strata": len(AGES),
        "standard_population": "registered electors in the 2023 turnout workbook",
        "standard_counts": references, "national_counts": TOTALS,
        "original_sha256": ORIGINAL_SHA, "normalised_input_sha256": NORMALISED_SHA,
        "analysis_status": "descriptive_retrospective_not_causal",
        "source_publication_time": None, "boundary_vintage": "2020",
        "rounding": "12 decimal places on exported percentages; 50-digit working precision",
        "limitations": [
            "An age-composition adjustment, not an estimate of how individuals would vote.",
            "Registered general and Maori roll populations differ from Census resident populations.",
            "These are conditional observed turnout patterns, not forecasts or causal effects.",
            "No uncertainty interval, spatial adjustment or unmeasured-confounder adjustment is claimed.",
        ],
        "published_to_hugging_face": False,
    }
    return result, receipt


def run(input_path: Path, output: Path) -> dict[str, Any]:
    """Write a new candidate directory and bind every output to the retained input."""
    rows, receipt = standardise(load_rows(input_path))
    output.mkdir(parents=True, exist_ok=False)
    (output / "age-standardised-turnout-2023.json").write_text(
        json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    with (output / "age-standardised-turnout-2023.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    receipt["outputs_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in sorted(output.iterdir())}
    (output / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
                                          encoding="utf-8")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.input, args.output), ensure_ascii=False, indent=2))
