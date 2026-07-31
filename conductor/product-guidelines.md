# Product Guidelines

## Communication principles

Archive Govt NZ communicates in an evidence-first, technically precise voice.
Documentation must use plain language, exact status labels, reproducible commands,
and explicit uncertainty.

Never imply that a dataset is complete, preserved, published, current, or
recoverable without evidence supporting that specific claim.

## Evidence before status

Operational reporting uses a stage-based evidence ledger. Report these states
separately rather than collapsing them into a single success label:

- discovered
- eligible
- capture attempted
- captured
- integrity validated
- transformed
- derivative validated
- uploaded
- remotely verified
- released
- unchanged
- unavailable
- withdrawn
- restricted
- failed

Each applicable state should identify its observation time, responsible process,
stable object identifier, supporting receipt, and known limitation.

A successful workflow run is evidence that a process executed. It is not, by
itself, proof that every intended dataset was captured or that an external
publication is available and correct.

## Human-readable and machine-readable pairs

Major reports and receipts should be available in complementary forms:

- concise Markdown for maintainers, researchers, and reviewers;
- versioned JSON for automation and reconciliation;
- published JSON Schema for validation;
- stable identifiers linking summaries, manifests, objects, transformations,
  releases, and external records.

The machine-readable artefact is the precise state record. The human-readable
artefact explains its meaning, material exceptions, and required action. They
must be generated or reconciled from the same evidence.

## Provenance presentation

For every archived object, make it easy to determine:

- where it came from;
- when and how it was discovered and retrieved;
- which source identifiers and URLs applied;
- which bytes were received and their cryptographic hashes;
- what licence, rights, or access statements were observed;
- whether retrieval was complete, partial, blocked, or metadata-only;
- what transformations occurred;
- which tool versions, parameters, inputs, and outputs were involved;
- what validation was performed;
- where the object or derivative was published;
- whether the remote publication was independently verified.

Originals and derivatives must be visually and structurally distinct. Never
present a transformed representation as though it were the publisher's original.

## Failure communication

Failures are first-class archive observations. Reports should state:

1. the affected stable identifier;
2. the bounded failure category;
3. the stage at which it occurred;
4. whether safe retry is possible;
5. the latest attempt and next retry state;
6. the relevant redacted evidence reference;
7. the impact on coverage or publication claims.

Use direct labels such as `blocked_by_rights`, `source_unavailable`,
`checksum_mismatch`, `upload_unverified`, or `security_review_required`.
Avoid vague labels such as `done`, `mostly complete`, or `sync successful`
unless their scope is explicitly defined.

## Security and bounded disclosure

Default to fail-closed behaviour.

Logs, fixtures, reports, issues, CI artefacts, and publications must not expose:

- credentials, tokens, cookies, or authentication headers;
- signed or short-lived access URLs;
- personal information not already approved for preservation and publication;
- sensitive source payloads;
- local filesystem details that disclose unrelated private material;
- unredacted request or response bodies when metadata is sufficient.

Record actionable diagnostic classes, affected identifiers, status codes,
retry information, content hashes, and redacted evidence references instead.
Sensitive diagnostics remain local and access-controlled when retention is
necessary.

## Interface and automation conventions

- Commands should be non-interactive by default and support dry-run operation.
- Destructive, public, credentialed, or irreversible actions require explicit
  flags and clear previews.
- Repeated operations should be idempotent or provide deterministic
  reconciliation.
- Exit codes and structured output should distinguish success, partial success,
  unchanged state, policy restriction, retryable failure, and terminal failure.
- Progress output must not leak secrets or overstate completeness.
- Defaults should be safe for a solo maintainer and CI execution.

## Documentation structure

Documentation should lead with the current outcome and evidence, followed by
limitations and reproduction steps. Use diagrams only when they clarify
architecture, state transitions, provenance relationships, or recovery paths.

Conductor requirements use MoSCoW priorities. Design-bearing tracks include
Mermaid diagrams and explain trust boundaries, data flows, failure paths, and
publication gates.

## Accessibility and durability

- Prefer portable Markdown, JSON, JSON Schema, and open archival formats.
- Do not rely on colour alone to communicate state.
- Give diagrams and generated reports meaningful text descriptions.
- Use stable headings, identifiers, filenames, and links.
- State units, encodings, time zones, timestamp formats, and hash algorithms.
- Prefer deterministic generation so artefacts can be compared and rebuilt.
