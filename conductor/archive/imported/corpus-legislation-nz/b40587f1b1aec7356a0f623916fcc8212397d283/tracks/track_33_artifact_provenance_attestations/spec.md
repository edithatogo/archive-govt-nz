# Spec - Artifact Provenance And Attestations

## Status
done

## Goal

Add release evidence ledgers, GitHub artifact attestations or SLSA-style provenance, and signed/checksummed artifact policy.

## Acceptance Criteria

- Aligns with `docs/bleeding-edge-versioning-ci-quality.md`.
- Preserves `corpus-nz-legislation` and `corpus-nz-hansard` naming.
- Uses Rust-backed tooling where practical: `uv`, `ruff`, `ty`, `typos`, `zizmor`, `taplo`, and local `ripgrep` guidance.
- Defines a release evidence ledger covering commit SHA, workflow run, Hugging Face revision, Zenodo DOI/concept DOI where applicable, manifest hash, checksums, schema version, record count, and coverage statement.
- Adds an explicit decision on GitHub artifact attestations, SLSA-style provenance, or signed/checksummed artifacts for each release artifact class.
- Keeps publication to Hugging Face and Zenodo behind validation gates.
- For Zenodo work, uses or formally evaluates `https://github.com/zenodraft/zenodraft`.

## Completion Evidence

- Provenance policy:
  `docs/artifact_provenance_attestations.md`.
- Release evidence schema:
  `schemas/release_evidence.schema.json`.
- Release evidence generator:
  `src/nz_legislation_corpus/artifact_provenance.py`.
- Archive generation now emits
  `corpus-legislation-nz-YYYY.release-evidence.json` and includes it in
  `SHA256SUMS`.
- Annual Zenodo archive workflow uploads archive evidence artifacts and calls
  GitHub artifact attestations before the Zenodo draft upload step.
- Consistency checker:
  `scripts/check_artifact_provenance.py`.
- Tests:
  `tests/test_artifact_provenance.py`.
