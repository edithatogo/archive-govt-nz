"""Tests for contract validation tool."""

from __future__ import annotations

from typing import TYPE_CHECKING
from tools.validate_contracts import validate_contract_dict

if TYPE_CHECKING:
    from pathlib import Path


def test_validate_contract_dict_valid(tmp_path: Path) -> None:
    """Test validating a well-formed contract dictionary."""
    contract = {
        "contract_id": "test-contract",
        "version": "1.0.0",
        "status": "active",
        "scope": "Test contract scope",
        "owning_track": "track_test",
        "baseline": {
            "audited_target_commit": "c" * 40,
            "audited_donor_commit": "7" * 40,
        },
        "invariants": ["Invar 1"],
        "preconditions": ["Pre 1"],
        "postconditions": ["Post 1"],
        "forbidden_actions": ["No bad stuff"],
        "acceptance_checks": [
            {
                "check_id": "CHK-01",
                "description": "Test check",
                "command": "true",
                "expected_exit_code": 0,
            }
        ],
        "evidence_paths": ["evidence/test.json"],
        "created_at": "2026-08-18T12:00:00Z",
        "updated_at": "2026-08-18T12:00:00Z",
    }
    dummy_file = tmp_path / "test.yaml"
    errs = validate_contract_dict(contract, dummy_file)
    assert len(errs) == 0


def test_validate_contract_dict_invalid(tmp_path: Path) -> None:
    """Test validating an invalid contract dictionary."""
    contract = {
        "contract_id": "bad-contract",
        "baseline": {
            "audited_target_commit": "bad-sha",
            "audited_donor_commit": "bad-sha",
        },
        "created_at": "2099-01-01T00:00:00Z",  # Future timestamp
        "acceptance_checks": [
            {
                "check_id": "CHK-01",
                # missing description, command, expected_exit_code
            }
        ],
    }
    dummy_file = tmp_path / "bad.yaml"
    errs = validate_contract_dict(contract, dummy_file)
    assert len(errs) >= 4
