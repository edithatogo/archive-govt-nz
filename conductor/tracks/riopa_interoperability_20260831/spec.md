# RIOPA Interoperability Integration

## Overview

Add a bounded bridge from `archive-govt-nz` preservation and replay receipts to
RIOPA source/capture evidence using immutable archive records only.

## Requirements

- Emit deterministic mappings from archive receipts to RIOPA source/capture records.
- Preserve original bytes, digests, partial/negative attempts and correction history.
- Carry rights, source-health, capability and legal-status observations without inference.
- Support Python 3.14 and the existing validation harness.
- Keep network, timetable, facility, national, clinical, dispatch and authoritative claims disabled.

## Acceptance criteria

1. A schema-valid export maps an archive receipt to content-addressed RIOPA records.
2. Replay/fixity validation fails closed on digest, revision, rights or visibility drift.
3. Partial and negative attempts remain inspectable and cannot be promoted.
4. Tests cover deterministic output, stale revisions and disabled claims.
5. Hosted validation evidence is recorded; no publication or release is implied.

## External gates

External participant reproduction, elapsed beta/RC soak, production recovery,
national-scale measurement and accountable release authority remain outside this
track and must not be represented as complete by local tests.

## Out of scope

Live endpoint acquisition, payload redistribution without exact rights evidence,
operational service claims, stable-v1 promotion and unrelated domain changes.

## Authoritative inputs

- `conductor/requirements.md`
- `conductor/workflow.md`
- `src/archive_govt_nz/riopa/`
- RIOPA contracts: `https://github.com/edithatogo/riopa-infrastructure`
