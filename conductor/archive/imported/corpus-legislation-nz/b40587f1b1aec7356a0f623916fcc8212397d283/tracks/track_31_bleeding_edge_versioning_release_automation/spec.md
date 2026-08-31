# Spec - Bleeding Edge Versioning And Release Automation

## Status
done

## Goal

Implement SemVer/dataset/schema version governance, Release Please-style changelog automation, and consistency checks.

## Acceptance Criteria

- Aligns with `docs/bleeding-edge-versioning-ci-quality.md`.
- Preserves `corpus-nz-legislation` and `corpus-nz-hansard` naming.
- Uses Rust-backed tooling where practical: `uv`, `ruff`, `ty`, `typos`, `zizmor`, `taplo`, and local `ripgrep` guidance.
- Defines separate code/package, dataset, schema, Hugging Face revision, Zenodo DOI snapshot, and manifest-hash version authorities.
- Adds consistency checks for version-bearing files such as `pyproject.toml`, release notes, `CITATION.cff`, dataset cards, manifests, and Zenodo/Hugging Face metadata.
- Records whether Release Please or an equivalent changelog/tag automation is adopted, deferred, or rejected with reasons.
- Keeps publication to Hugging Face and Zenodo behind validation gates.
- Keeps release automation evidence-only until protected environments and publication gates are proven.
- For Zenodo work, uses or formally evaluates `https://github.com/zenodraft/zenodraft`.

## Completion Evidence

- Version governance document:
  `docs/versioning_release_automation.md`.
- Consistency checker:
  `scripts/check_version_consistency.py`.
- Tests:
  `tests/test_version_consistency.py`.
- CI enforcement:
  `.github/workflows/tests.yml` runs
  `uv run python scripts/check_version_consistency.py` with read-only
  repository permissions.
- Release Please decision: deferred. Future Release Please-style automation may
  propose package changelog/version PRs, but it must not publish Hugging Face
  datasets or Zenodo records.
- Zenodo draft tooling: Track 27 formally evaluated `zenodraft`; Track 31 keeps
  the DOI/version authority and draft-first publication gate in the release
  model.
