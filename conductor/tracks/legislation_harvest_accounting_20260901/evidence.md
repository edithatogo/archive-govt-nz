# Evidence

Initial target main `bd53d7c71f6f0d366d337365f751e44d1c9b2995`; no audited Prompt 12 SHA was supplied. Donor final reachable head and archived status must be recorded in the issue closeout evidence.

Initial audit found that `works_attempted` counted resolved scope, including checkpoint-skipped works; `works_synced` counted newly processed work IDs; and `records_preserved` counted records returned during the run rather than manifest or CAS deltas. Partial service runs could persist manifest and checkpoint state while the runner reported `state_committed: false`. Retry counts and source-response classifications were discarded, and search-resolution failures could disappear before accounting.

Validation and delivery evidence will be appended without replacing failed attempts or historical receipts.

The donor was independently re-read as archived at final reachable head `b40587f1b1aec7356a0f623916fcc8212397d283`. Target `main` advanced after work began to `0c3afba452b26d7721e75310b2e4d2b19d82782f`; that exact state was merged into the issue branch before final validation.

Focused accounting, API, service, runner, CAS, and CLI tests passed: 206 tests. The first full harness attempt ran 4,372 tests at 97.40% total coverage and failed only because the assurance-stage sequence fixture did not yet include the new mutation stage. The fixture was corrected, preserving the failed attempt here. The repeated complete harness passed all 4,372 tests, 45 schemas, 35 representative documents, 9/9 parity checks, every repository mutation lane, dependency audit, licence inventory, secret scan, and SBOM validation. The changed accounting module reached 100% statement and branch coverage; the full repository reached 97.40%.

The Prompt 12 mutation receipt killed 13/13 mutants. Its accounting source hash is `1a0088c7eee11b7566684a9755c8eb5b0eec4aec06f53ceee9c57d41d0e37334`. The v3 schema hash is `436c20386263466fb96b763db253677bfc434cc1b0e9241aff623b3e04dec67c`; the representative receipt hash is `295fe7566e4f736dce624f4e7fa1ba610c0ef39ea70d9e8ea646ae45d57dd2b3`; and the mutation runner hash is `e10de62876e17986dd32806404781fb6b867fc068c11649163e15a5f3f59705d`.
