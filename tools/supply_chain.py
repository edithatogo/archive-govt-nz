"""Run fail-closed local supply-chain controls and emit bounded receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING, cast

from cyclonedx.schema import SchemaVersion
from cyclonedx.validation.json import JsonStrictValidator

from archive_govt_nz.licensing import licence_denial

if TYPE_CHECKING:
    from collections.abc import Sequence

REPOSITORY_ROOT = Path(__file__).parents[1]
BUILD_DIRECTORY = REPOSITORY_ROOT / "build"
CONTROL_NAMES = ("audit", "licenses", "secrets", "sbom")
EXCLUDED_PATH_PATTERN = (
    r"(?:^|[\\/])(?:\.git|\.venv|\.pytest_cache|\.ruff_cache|build|coverage|dist|htmlcov)"
    r"(?:[\\/]|$)"
    r"|(?:^|[\\/])\.coverage(?:\.[^\\/]*)?$"
    r"|uv\.lock$"
    r"|conductor[\\/]tracks[\\/].*[\\/](?:evidence|runlog)\.md$"
    r"|conductor[\\/]archive[\\/]imported[\\/].*"
)
RECEIPT_EXCLUSION_PATTERN = (
    r'"(?:[a-z_]*revision(?:_[a-z_]+)?|[a-z_]*commit|[a-z_]*sha256|fingerprint|previous_fingerprint|workspace_dir)"\s*:'
    r'|"detail"\s*:\s*"[0-9a-f]{40}"'
    r'|"[0-9a-f]{40}"'
    r'|"[0-9a-f]{64}"'
    r"|consolidation_revision"
)

# Reviewed public lineage documents, not a general path or entropy exemption.
# Changed documents require review again; donor snapshots and receipts stay intact.
PUBLIC_LINEAGE_DOCUMENTS = {
    "donor-track-lineage.json": (
        "177d479c3ec6ee6eef3e98ccdda230cd505ccf3797921783d96748f8bb8e58a1"
    ),
    "import-fixity.json": (
        "6e9f9bcbd70ac2adaf6358df50c5c024165c619ae298e9c747f39b58cbe00977"
    ),
    "receipt-precommit.json": (
        "9c337b834654e0cf17f6513390c46a4cf1dcf5b5dca091bd9aa0fe67e0cd6449"
    ),
    "receipt.json": "7a90eed0dabd874a835d31a29c42eec52c5c6b3cd2623aa0436e563df53ac52b",
}
PUBLIC_LINEAGE_ROOT = "evidence/migrations/corpus-legislation-nz/final-lineage/"
PUBLIC_IMPORT_VALUE = re.compile(
    r'"(?:previous_import|final_import|imported_root|imported_tree_root)"\s*:\s*'
    r'"(conductor/archive/imported/corpus-legislation-nz/'
    r"(?:749918c251da59dc890c19dfda2ab9a021fd8ca6|b40587f1b1aec7356a0f623916fcc8212397d283)"
    r'(?:/(?:tracks|archive)/[a-z0-9_]+)?)"'
)
PUBLIC_EVIDENCE_INDEX = "evidence/migrations/corpus-legislation-nz/evidence-index.json"
PUBLIC_CHECKSUM_PATH = (
    "evidence/migrations/corpus-legislation-nz/final-donor-state/"
    "verification-01/SHA256SUMS"
)
PUBLIC_CHECKSUM_PATH_CANDIDATE_DIGEST = "202980b9d847d8c9f1af423526b0383990e8e0d7"


def _is_indexed_public_checksum_path(relative: str, finding: dict[str, object]) -> bool:
    if (
        relative != PUBLIC_EVIDENCE_INDEX
        or finding.get("type") != "Base64 High Entropy String"
        or finding.get("hashed_secret") != PUBLIC_CHECKSUM_PATH_CANDIDATE_DIGEST
    ):
        return False
    try:
        index = json.loads((REPOSITORY_ROOT / relative).read_text(encoding="utf-8"))
        return any(
            row.get("path") == PUBLIC_CHECKSUM_PATH
            for row in cast("list[dict[str, object]]", index.get("entries", []))
        )
    except OSError, UnicodeError, json.JSONDecodeError, AttributeError:
        return False


def is_reviewed_public_path(filename: str, finding: dict[str, object]) -> bool:
    """Adjudicate only an exact path candidate in an unchanged reviewed document."""
    relative = filename.replace("\\", "/")
    if _is_indexed_public_checksum_path(relative, finding):
        return True
    allowed = {
        PUBLIC_LINEAGE_ROOT + name: digest
        for name, digest in PUBLIC_LINEAGE_DOCUMENTS.items()
    }
    if relative not in allowed or finding.get("type") != "Base64 High Entropy String":
        return False
    path = REPOSITORY_ROOT / relative
    try:
        payload = path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != allowed[relative]:
            return False
        number = finding.get("line_number")
        lines = payload.decode("utf-8").splitlines()
        if type(number) is not int or not 1 <= number <= len(lines):
            return False
        return any(
            hashlib.sha1(match[1].encode(), usedforsecurity=False).hexdigest()
            == finding.get("hashed_secret")
            for match in PUBLIC_IMPORT_VALUE.finditer(lines[number - 1])
        )
    except OSError, UnicodeError:
        return False


def run(command: Sequence[str], *, capture: bool = False) -> str:
    """Run one repository-owned command and fail on a nonzero status."""
    result = subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=capture,
        text=True,
    )
    if result.returncode != 0:
        if capture:
            print(result.stdout, end="")
            print(result.stderr, end="")
        raise SystemExit(result.returncode)
    return result.stdout


def audit() -> None:
    """Audit the locked environment and retain a machine-readable receipt."""
    output_path = BUILD_DIRECTORY / "pip-audit.json"
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            run(
                (
                    "pip-audit",
                    "--local",
                    "--skip-editable",
                    "--progress-spinner=off",
                    "--timeout=60",
                    "--vulnerability-service=osv",
                    "--format=json",
                    f"--output={output_path}",
                )
            )
            break
        except SystemExit:
            if attempt == max_attempts:
                raise
            time.sleep(2 * attempt)
    print(
        f"dependency audit passed; receipt={output_path.relative_to(REPOSITORY_ROOT)}"
    )


def licenses() -> None:
    """Inventory installed licences and reject unresolved or strong copyleft."""
    output = run(("pip-licenses", "--format=json"), capture=True)
    records = cast("list[dict[str, object]]", json.loads(output))
    denied: list[str] = []
    for record in records:
        name = str(record.get("Name", "<unnamed>"))
        licence = str(record.get("License", ""))
        denial = licence_denial(name, licence)
        if denial is not None:
            denied.append(f"{name}: {licence.casefold()} ({denial})")
    output_path = BUILD_DIRECTORY / "python-licenses.json"
    output_path.write_text(
        json.dumps(records, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if denied:
        print("denied or unresolved licences:")
        print("\n".join(sorted(denied)))
        raise SystemExit(1)
    print(
        f"licence inventory passed; receipt={output_path.relative_to(REPOSITORY_ROOT)}"
    )


def secrets() -> None:
    """Scan tracked-source scope and fail when candidate secrets remain."""
    output = run(
        (
            "detect-secrets",
            "scan",
            "--force-use-all-plugins",
            "--exclude-files",
            EXCLUDED_PATH_PATTERN,
            "--exclude-lines",
            RECEIPT_EXCLUSION_PATTERN,
        ),
        capture=True,
    )
    receipt = cast("dict[str, object]", json.loads(output))
    output_path = BUILD_DIRECTORY / "detect-secrets.json"
    output_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    results = receipt.get("results")
    if not isinstance(results, dict):
        message = "detect-secrets returned an invalid results envelope"
        raise SystemExit(message)
    typed_results = cast("dict[str, object]", results)
    adjudicated = []
    finding_count = 0
    for filename, findings in typed_results.items():
        if not isinstance(findings, list) or any(
            not isinstance(finding, dict) for finding in findings
        ):
            message = "detect-secrets returned invalid findings"
            raise SystemExit(message)
        for finding in cast("list[dict[str, object]]", findings):
            if is_reviewed_public_path(filename, finding):
                adjudicated.append({"filename": filename, **finding})
            else:
                finding_count += 1
    (BUILD_DIRECTORY / "secret-adjudications.json").write_text(
        json.dumps(
            {"reviewed_public_paths": adjudicated, "unresolved_count": finding_count},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    if finding_count:
        print(f"secret scan found {finding_count} candidate(s); inspect {output_path}")
        raise SystemExit(1)
    print(f"secret scan passed; receipt={output_path.relative_to(REPOSITORY_ROOT)}")


def sbom() -> None:
    """Generate and structurally validate a reproducible CycloneDX SBOM."""
    output_path = BUILD_DIRECTORY / "sbom.cdx.json"
    run(
        (
            "cyclonedx-py",
            "environment",
            "--spec-version",
            "1.6",
            "--output-format",
            "JSON",
            "--output-reproducible",
            # The mandatory strict validator below validates schema AND formats.
            # Avoid repeating the expensive IRI checks in the generator first.
            "--no-validate",
            "--output-file",
            str(output_path),
        )
    )
    document_text = output_path.read_text("utf-8")
    validation_error = JsonStrictValidator(SchemaVersion.V1_6).validate_str(
        document_text
    )
    if validation_error is not None:
        message = f"generated SBOM failed CycloneDX validation: {validation_error}"
        raise SystemExit(message)
    document = cast("dict[str, object]", json.loads(document_text))
    if document.get("bomFormat") != "CycloneDX":
        message = "generated SBOM has an unexpected format"
        raise SystemExit(message)
    components = document.get("components")
    if not isinstance(components, list) or not components:
        message = "generated SBOM has no components"
        raise SystemExit(message)
    typed_components = cast("list[object]", components)
    print(
        f"SBOM validated; components={len(typed_components)}; "
        f"receipt={output_path.relative_to(REPOSITORY_ROOT)}"
    )


def parse_arguments() -> argparse.Namespace:
    """Parse one non-interactive supply-chain control."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("control", nargs="?", choices=CONTROL_NAMES)
    parser.add_argument("--list", action="store_true", help="list available controls")
    return parser.parse_args()


def main() -> int:
    """Run the selected control or list the available controls."""
    arguments = parse_arguments()
    if arguments.list:
        print("\n".join(CONTROL_NAMES))
        return 0
    if arguments.control is None:
        message = "a control is required"
        raise SystemExit(message)
    controls = {
        "audit": audit,
        "licenses": licenses,
        "secrets": secrets,
        "sbom": sbom,
    }
    controls[arguments.control]()
    return 0


if __name__ == "__main__":
    BUILD_DIRECTORY.mkdir(parents=True, exist_ok=True)
    raise SystemExit(main())
