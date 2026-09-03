# Requirements

- **MUST** classify automatic Slack and Discord webhook payloads from parsed,
  exact endpoint components rather than caller-controlled URL substrings.
- **MUST** retain explicit service selection and generic webhook delivery.
- **MUST** cover deceptive host, user-info, and path substring cases.
- **MUST** preserve optional workflow argument boundaries without passing an
  empty argument.
- **MUST** pass focused tests, actionlint, the repository validation harness,
  and exact-head hosted checks.
- **MUST NOT** change branch protection, publication, archive state, secrets,
  harvest semantics, or unrelated Prompt 20 findings.
