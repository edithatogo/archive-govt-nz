# Contributing

This repository is maintained by one developer and accepts focused issues and
pull requests. Start with a reproducible problem statement, affected stable
identifiers, expected and observed behavior, bounded fixtures, and relevant
Conductor/GitHub references. Never attach credentials, signed URLs, personal
information, restricted payloads, or source files whose redistribution rights
are unclear.

Changes must preserve originals, provenance, explicit state semantics, and
fail-closed publication gates. Use test-driven increments and run:

```powershell
uv run --locked python tools/check.py
```

Commits use Conventional Commits and include issue and Conductor references.
The solo maintainer may author, self-review, and merge after automated evidence
passes; a fictional second-person approval is not required.

Disclose material AI assistance in the pull request or commit narrative,
including what was generated, how it was verified, and any uncertainty. The
human submitter remains accountable for rights, security, accuracy, tests, and
all external claims. Upstream CKAN-related contributions must additionally
follow that project's CLA/DCO, contribution, disclosure, and AI-use rules.
