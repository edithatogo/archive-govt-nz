# Requirements: RIOPA interoperability integration

## Must

- Map immutable archive receipts to RIOPA source and capture records.
- Preserve digest, revision, rights, capability, source-health and legal-status observations.
- Fail closed on stale, corrupt, partial or rights-unresolved inputs.
- Keep disabled operational and authoritative claims explicit.

## Should

- Emit JSON and JSON-LD representations where existing contracts permit.
- Support hosted replay evidence without publishing restricted payloads.

## Could

- Add a convenience CLI wrapper for downstream RIOPA consumers.

## Won't

- Contact live endpoints or broaden source authority.
- Promote beta, RC or stable-v1 releases.

## Acceptance

Schema validation, deterministic replay, negative-path tests, Python 3.14
validation and agent-panel review all pass.
