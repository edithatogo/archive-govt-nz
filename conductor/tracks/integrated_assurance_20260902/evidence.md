# Evidence

The receipt and supporting artefacts are under
`evidence/assurance/integrated-20260902/`.

Classification: **INCOMPLETE**. Local and exact-main hosted harnesses passed,
but open high-severity CodeQL alerts and actionlint failures violate Prompt 20
acceptance. Issue #354 separately records the absence of hosted enforcement.

## Superseding hosted-enforcement readback — 2026-09-03

The missing-enforcement finding routed to issue #354 is superseded by
`evidence/assurance/main-ruleset-20260903/`. Live GitHub readback at target
`b408aa3660b5de9d68fec31ef2273938226e5f18` verified active ruleset `22180861`
with strict Ubuntu, macOS, Windows, CodeQL `analyze`, workflow-policy `lint`, and
`codecov/patch` contexts. It requires review-thread resolution and zero
approving reviewers, matching the solo-maintainer policy. Repository-role actor
`5` retains the authorized auditable emergency bypass.

This closes the factual absence recorded in the original receipt without
rewriting it. Prompt 20 completion still depends on its other exact-head
assurance evidence and is not claimed by this update alone.

Hosted run `33740682306` is retained as a failed attempt: all three platform
jobs rejected a `Secret Keyword` candidate introduced by the receipt's
`secret_scan` metadata key. The corrective commit renames that assertion to
`credential_scan` and minimizes the raw API files to stable policy fields,
retaining source-response hashes in the normalized receipt. Scanner policy is
unchanged.
