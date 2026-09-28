# Canonical Gold dataset card

This local package projection makes product coverage inspectable without implying analytical completeness, rights eligibility, federation or publication.

The generated `dataset-card.md` reports, for each source-separated product, admitted input record count, output row count and exact-context temporal group count. It lists only the SHA-256 pins of canonical input package markers. It does not expose source labels, input record identities, citations, URLs or license assertions. The card is included in the canonical Gold manifest fixity inventory and in the RO-Crate `hasPart` inventory; it is excluded from its own contents.

The card states that analytical completeness is not evaluated; source health, classification drift and revision reconciliation remain unresolved; cross-source reconciliation has not been performed; rights have not been evaluated; and publication has not been performed. This is a descriptive local artifact, not a release or standards-conformance claim.

Focused verification: `uv run --locked python -m ruff check src/archive_govt_nz/domains/health_appropriations/canonical_gold_export.py tests/domains/health_appropriations/test_canonical_consumer.py`; canonical consumer tests passed 16/16 with 98.81% branch-aware module coverage. Full repository validation and hosted pull request checks are recorded after they complete.
