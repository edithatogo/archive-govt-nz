# 2016/17 Vote Health Estimates overview common dispatch

Issue: [#209](https://github.com/edithatogo/archive-govt-nz/issues/209),
Phase 3.2. This is a bounded adapter increment, not completion of Phase 3.

The reviewed 2016/17 overview parser now participates in the common Bronze
adapter registry. Registration is optional and bound to the exact source
vintage, SHA-256, PDF page count, and parser layout. Extraction emits the
existing 24 overview facts, value lineage, and a disposition for every one of
the 102 PDF pages. It preserves the established whole-million units, headline
scope, unresolved rights state, and source qualifiers. No Bronze bytes or
historical values were changed.

Unknown editions/layouts remain `preserved_only`; a caller-supplied SHA mismatch
is rejected. Tests cover exact-profile dispatch, fact/lineage/page counts,
provenance and rights state, and wrong-vintage fail-closed behavior. Broader
Vote Health PDF layouts, SQLite, classification mappings, donor workbook areas,
and the 30 source-backed historical differences remain open.

Required `./scripts/validate.sh`: pass. Tests: 7,480 passed, 10 skipped. Total
coverage: 97.77%, with the repository's 80% floor unchanged. Schema validation
covered 53 schemas and 43 representative documents; differential parity passed
9/9 with zero divergences. Configured mutation gates, hygiene, dependency and
licence audits, secret scan, and the 113-component SBOM passed. These checks
establish local repository assurance; hosted PR checks are still required.
