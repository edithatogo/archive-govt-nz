# Review

## Verdict

The local implementation and validation phases are approved for the bounded
global CLI scope at commit `7616ddb`.

## Findings resolved

- Replay traverses the production sharded CAS and rejects malformed or
  symlinked objects while using the streaming object-store verifier.
- Archive verification requires a closed fixity manifest and structurally
  valid WARC, compressed WARC, or WACZ content.
- Global verification inspects CAS, JSON Schemas, provenance, and the declared
  Python 3.14 runtime rather than directory presence.
- Provenance and search use validated domain structures and real semantic
  query execution.
- Publication preparation requires fixed non-empty files, an explicit target
  repository, and consistent cleared rights. It performs no remote side effect
  and does not treat a credential as readiness evidence.
- Legislation CLI, MCP, workflow, live execution, publication authority,
  redistribution rights, recovery, cutover, and donor archival were not
  advanced by this track.

## Review-fix finding

- **High — operator contract drift:** `README.md` advertised standalone capture
  and manifest-free archive verification, `docs/operations/runbook.md` treated
  the currently non-operational scheduled workflow and capture command as live
  harvesting, and `docs/migrations/sm-govt-nz/interface-map.md` specified a
  nested grammar and `--json` flag that the CLI does not implement. The README
  also claimed the donor was archived, contrary to the required recovery gate
  and current GitHub state. Phase 4A corrects these documents without advancing
  the separately sequenced workflow, publication, rights, or donor gates.
  **Resolved in `ab81d80`**: the documents now use the implemented flat grammar
  and `--format json`, require explicit manifest/CAS/provenance paths, describe
  capture and workflow as not operational, preserve publication and rights
  boundaries, and state that the donor remains unarchived. A regression test
  covers the superseded grammar and claims. The full locked harness passed after
  the correction.

## Remaining gate

Phase 5 is intentionally pending. The branch is local-only and must not be
pushed or opened as a second PR while service-correction PR #156 remains open.
After that service correction is permitted to merge, rebase this branch onto
current `main`, rerun the full harness, and conduct fresh review before opening
the single global CLI successor PR.

The repository-wide Conductor validator still reports pre-existing
control-plane defects (missing `conductor/vcs.md` and index links, legacy
metadata, and registry parsing mismatches). Those are separate from this
bounded code verdict and remain unresolved.
