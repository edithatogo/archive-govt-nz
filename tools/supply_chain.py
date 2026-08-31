"""Run fail-closed local supply-chain controls and emit bounded receipts."""

from __future__ import annotations

import argparse
import json
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
    finding_count = sum(
        len(cast("list[object]", findings))
        for findings in typed_results.values()
        if isinstance(findings, list)
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
