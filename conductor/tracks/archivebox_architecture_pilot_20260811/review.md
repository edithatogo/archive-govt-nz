# Review Report: ArchiveBox preservation pilot and reusable architecture

## Summary

The track satisfies its bounded pilot and architecture requirements; ArchiveBox
is useful as a manual secondary exception lane but did not verify any original
payload in the hosted trial.

## Verification Checks

- [x] **Plan Compliance**: Yes - all Must requirements and acceptance criteria
  have local or hosted evidence.
- [x] **Style Compliance**: Pass - Ruff, strict Pyright, and repository guidance
  pass.
- [x] **New Tests**: Yes - unit, property, metamorphic, contract, deterministic
  simulation, integration, and workflow-policy tests.
- [x] **Test Coverage**: Yes - 96.13% repository branch coverage and 100% line
  and branch coverage for the pilot policy module.
- [x] **Test Results**: Passed - 330 tests plus schema and supply-chain gates.

## Resolved findings

### Medium: file inventory did not explain per-candidate extractor failures

The first successful hosted run hashed output files but could allow WARC file
presence to be misunderstood as a successful source capture. Commit `3fdf3c0`
added bounded per-snapshot parsing, exact candidate reconciliation, redacted
extractor states, access-challenge classification, and explicit
`original_payload_verified=false`. The corrected hosted run verified the fix.

## External publication observation

The architecture is present in canonical repository documentation, generated
Hugging Face card material, and future Zenodo package inputs. The current
Hugging Face credential identifies the account but lacks permission for direct
writes and PR pre-upload; no remote write occurred. Track 16 explicitly excludes
automatic payload publication and a documentation-only DOI.

## Decision

Complete the track and retain ArchiveBox as a manually dispatched exception
lane. Do not schedule it, admit the current outputs, or treat WARC files as
publisher originals.
