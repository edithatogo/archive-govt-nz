# Evidence

Initial target main `bd53d7c71f6f0d366d337365f751e44d1c9b2995`; no audited Prompt 12 SHA was supplied. Donor final reachable head and archived status must be recorded in the issue closeout evidence.

Initial audit found that `works_attempted` counted resolved scope, including checkpoint-skipped works; `works_synced` counted newly processed work IDs; and `records_preserved` counted records returned during the run rather than manifest or CAS deltas. Partial service runs could persist manifest and checkpoint state while the runner reported `state_committed: false`. Retry counts and source-response classifications were discarded, and search-resolution failures could disappear before accounting.

Validation and delivery evidence will be appended without replacing failed attempts or historical receipts.

The donor was independently re-read as archived at final reachable head `b40587f1b1aec7356a0f623916fcc8212397d283`. Target `main` advanced after work began to `0c3afba452b26d7721e75310b2e4d2b19d82782f`; that exact state was merged into the issue branch before final validation.

Focused accounting, API, service, runner, CAS, and CLI tests passed: 206 tests. The first full harness attempt ran 4,372 tests at 97.35% total coverage and failed only because the assurance-stage sequence fixture did not yet include the new mutation stage. The fixture was corrected, preserving the failed attempt here. The repeated complete harness passed all 4,392 tests, 45 schemas, 35 representative documents, 9/9 parity checks, every repository mutation lane, dependency audit, licence inventory, secret scan, and SBOM validation. The changed accounting module reached 100% statement and branch coverage; the full repository reached 97.35%.

The Prompt 12 mutation receipt killed 13/13 mutants. Its accounting source hash is `73be2a1f1c0363b190303fb68a2fe66a5482d8717571e3c4c5b360181f97f95f`. The v3 schema hash is `436c20386263466fb96b763db253677bfc434cc1b0e9241aff623b3e04dec67c`; the representative receipt hash is `295fe7566e4f736dce624f4e7fa1ba610c0ef39ea70d9e8ea646ae45d57dd2b3`; and the final portable mutation runner hash is `ed222a78058059b2fb049a53b40ccfc6b42295594fe5510852f7fb9c6b3066a5`.

Independent agent review found three blocking gaps after the first green local
gate: manifest promotion preceded checkpoint promotion, discovery preceded
strict checkpoint validation, and the v2 reader retained only three fields.
The repair reverses the parent-validation ordering, represents checkpoint
promotion failure as indeterminate without publishing the manifest, and
retains the complete original v2 mapping without assigning v3 meaning. The
focused repaired suite passed 111 tests.

The first hosted patch-coverage result at head `4cfeaf5d53b92e721088ce0c02bb8065e2c8e159` failed at 94.46254% with 17 changed lines uncovered. Focused terminal-disposition, retry, classification, transactional rollback and compatibility tests were added; no threshold or gate was weakened. Final exact-head hosted results are recorded at closeout.

Hosted run `33503994121` on coverage-repair head
`fc3806f6bac9d3126d5f2ed948c1bbad263b0663` passed Linux and macOS assurance
and caused the Codecov patch gate to pass. CodeQL, workflow policy lint,
dependency review, and analysis also passed on that head. The Windows job was
still running when this closeout-only evidence commit superseded the head; the
complete three-platform matrix is therefore required again on the final PR
head before merge.


The first final-head Windows job exposed a platform-specific hard-coded
`.venv/bin/python` path in the new mutation runner. Commit `d6470ef6` replaced
that path with the running interpreter (`sys.executable`); this is a tooling
portability correction and does not change the mutants or acceptance logic.
