"""Historical Gold preserves source and donor observations with explicit dispositions."""

import json
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from archive_govt_nz.domains.health_appropriations.historical_gold_donor_control import (
    reconcile_rows,
)


def test_reconciliation_accounts_for_gold_and_accepted_differences() -> None:
    gold = [
        {
            "record_id": "one",
            "year": 1976,
            "exact_amount": Decimal("605.70000000000005"),
            "source_context_json": '{"measure":"health_spending","source_object_sha256":"abc","year_label":"1976"}',
        }
    ]
    comparison = [
        {
            "measure": "health_spending",
            "year": 1976,
            "source_record_id": "one",
            "source_object_sha256": "abc",
            "source_coordinate": "H9",
            "source_year_label": "1976",
            "source_value": "605.70000000000005",
            "donor_value": "605.7",
            "delta": "5E-14",
            "status": "value_difference",
            "reason": "source_numeric_value_differs_from_donor",
            "resolution": "retain_both_observations",
        }
    ]
    entry = {
        **{
            key: comparison[0][key]
            for key in (
                "source_record_id",
                "source_object_sha256",
                "source_coordinate",
                "source_year_label",
                "status",
                "reason",
                "resolution",
            )
        },
        "source_value_sha256": sha256(b"605.70000000000005").hexdigest(),
        "donor_value_sha256": sha256(b"605.7").hexdigest(),
        "disposition": "accepted",
        "replacement_value": None,
        "publication_approved": False,
        "disposition_basis": "sqlite_real_retains_binary_value_not_decimal_token",
    }
    report = reconcile_rows(gold, comparison, [entry])
    assert report["counts"] == {"value_difference": 1}
    assert report["rows"][0]["source_value"] == "605.70000000000005"
    assert report["rows"][0]["donor_value"] == "605.7"
    assert report["rows"][0]["resolution"] == "retain_both_observations"
    with pytest.raises(ValueError, match="historical_gold_control_invalid"):
        reconcile_rows(gold, comparison, [{**entry, "replacement_value": "605.7"}])
    with pytest.raises(ValueError, match="historical_gold_control_invalid"):
        reconcile_rows(gold, comparison, [])
    with pytest.raises(ValueError, match="historical_gold_control_invalid"):
        reconcile_rows(gold + gold, comparison, [entry])
    with pytest.raises(ValueError, match="historical_gold_control_invalid"):
        reconcile_rows([{**gold[0], "exact_amount": Decimal(1)}], comparison, [entry])


def test_pinned_packages_repeat_and_reject_tampering(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from archive_govt_nz.domains.health_appropriations.historical_gold_donor_control import (  # noqa: PLC0415
        reconcile_packages,
    )

    gold = tmp_path / "gold"
    comparison = tmp_path / "comparison"
    gold.mkdir()
    comparison.mkdir()
    context = json.dumps(
        {
            "measure": "health_spending",
            "source_object_sha256": "a" * 64,
            "year_label": "2000",
        }
    )
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "record_id": "one",
                    "year": 2000,
                    "exact_amount": Decimal("1.0"),
                    "source_context_json": context,
                }
            ]
        ),
        gold / "historical_nominal.parquet",
    )
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "measure": "health_spending",
                    "year": 2000,
                    "source_record_id": "one",
                    "source_object_sha256": "a" * 64,
                    "source_coordinate": "H1",
                    "source_year_label": "2000",
                    "source_value": "1.0",
                    "donor_value": "1",
                    "delta": "0",
                    "status": "exact_match",
                    "reason": "exact_numeric_match",
                    "resolution": "retain_both_observations",
                }
            ]
        ),
        comparison / "comparison.parquet",
    )

    def pin(path: Path) -> str:
        return sha256(path.read_bytes()).hexdigest()

    def write(path: Path, payload: object) -> str:
        path.write_text(json.dumps(payload, sort_keys=True))
        return pin(path)

    gp = write(
        gold / "MANIFEST.json",
        {
            "schema_version": "archive-govt-nz.health-raw-gold/v1",
            "status": "passed",
            "output_sha256": {
                "historical_nominal.parquet": pin(gold / "historical_nominal.parquet")
            },
            "row_counts": {"historical_nominal.parquet": 1},
        },
    )
    cp = write(
        comparison / "MANIFEST.json",
        {
            "schema_version": "archive-govt-nz.health-historical-reconciliation-manifest/v1",
            "donor_object_sha256": "b" * 64,
            "counts": {"exact_match": 1},
            "output_sha256": {
                "comparison.parquet": pin(comparison / "comparison.parquet")
            },
        },
    )
    ledger = tmp_path / "dispositions.json"
    dp = write(
        ledger,
        {
            "schema_version": "archive-govt-nz.health-historical-dispositions/v1",
            "donor_database_sha256": "b" * 64,
            "comparison_counts": {"exact_match": 1},
            "disposition": "accepted_retain_both_no_replacement",
            "entries": [],
        },
    )
    args = (gold, gp, comparison, cp, ledger, dp)
    from archive_govt_nz.cli import app  # noqa: PLC0415

    first = reconcile_packages(*args)
    command = [
        "health-appropriations-reconcile-historical-gold",
        "--gold-root",
        str(gold),
        "--gold-manifest-sha256",
        gp,
        "--comparison-root",
        str(comparison),
        "--comparison-manifest-sha256",
        cp,
        "--dispositions-path",
        str(ledger),
        "--dispositions-sha256",
        dp,
    ]
    assert app(command, exit_on_error=False, result_action="return_value") == 0
    assert json.loads(capsys.readouterr().out) == first
    assert first == reconcile_packages(*args)
    assert first["counts"] == {"exact_match": 1}
    (gold / "historical_nominal.parquet").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="input_digest_mismatch"):
        reconcile_packages(*args)
    assert app(command, exit_on_error=False, result_action="return_value") == 2
    assert json.loads(capsys.readouterr().out)["status"] == "failed"
