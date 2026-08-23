# Evidence

- Stacked base: global CLI squash merge `138b17f`, incorporating service squash
  merge `394f210`.
- Merged CLI under correction: `src/archive_govt_nz/cli.py` legislation
  handlers introduced through PR #151.
- Corrected service and global CLI dependencies are merged through PRs #156 and
  #157 respectively.
- Implementation commit after rebase: `4d2e20c`.
- Critical authenticated-state module: 100% line and branch coverage across 18
  focused adversarial tests.
- CLI contract: 43 focused CLI tests passed; useful PR #151 command names,
  JSON fields, and bounded compatibility mappings are retained only where
  truthful.
- Affected suite: 119 tests passed across service, models, object store, CLI,
  and contract validation; all 15 contracts validated.
- Post-rebase integration audit found two inherited CLI tests still bypassed
  canonical discovery. They now supply canonical Work, Expression, and
  Manifestation graphs and pass through the corrected service path.
- Exact post-fix harness: 756 tests passed at 95.62% overall coverage; lock,
  format, lint, typing, schemas, all mutations, hygiene, CAS benchmark,
  dependency audit, licence inventory, secret scan, and SBOM passed.
- Post-merge-base harness: 756 tests passed at 95.62% overall coverage, with all
  repository gates green.
- Late PR #158 Codecov patch status reported 84.44% against a 94.88% target
  after the required hosted checks had completed and the merge was accepted.
  Corrective test commit `fb62c84` exercises the previously uncovered text,
  service-exception, incomplete, invalid, and unverified branches. The full
  harness now passes 762 tests at 96.12% overall coverage; a local executable
  source-line audit of the original PR #158 diff reports 180/180 lines hit.
- No live or remote affirmative evidence was generated.
