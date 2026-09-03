# Review

## Candidate review

- **Security boundary:** pass. Automatic classification now uses parsed
  hostname and, for Discord, the exact webhook path prefix. Host-suffix,
  user-info, and path-substring placements remain generic.
- **Compatibility:** pass. Exact Slack and Discord auto-detection, explicit
  service selection, and generic webhook delivery are exercised.
- **Workflow semantics:** pass. Empty arrays expand to zero arguments, while a
  supplied value remains one quoted argument after its option.
- **Scope:** pass. No branch protection, publication, state, harvest policy, or
  unrelated Prompt 20 path changed.
- **Remaining gate:** exact-head hosted CodeQL and CI readback.
