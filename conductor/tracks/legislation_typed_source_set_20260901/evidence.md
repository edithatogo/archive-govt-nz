# Evidence

Initial target main `cf2ec75b88963352abbecb89a2b8e2cfe538a070`; no audited SHA supplied. Donor independently observed archived at `b40587f1b1aec7356a0f623916fcc8212397d283`.

Before delivery, target main advanced through Prompt 09 to `d3946b8f5380c60b11b5f6e803f7188fc7d8e8df`; this track was rebased onto that exact head and retained the durable-state track registry entry.

Inventory: legislation.yml v1 fields were name, description, enabled, adapters, execution_mode, schedule, checkpoint_location, rights_class, nested output preservation (format/compression/CAS hash/retention), and nested HF/Zenodo policy. `source_sets.py` ignored all nested policy; `run_legislation_harvest.py` independently ignored indentation and parsed only top-level scalars. Generic capture consumed enabled/name, string adapters, targets and dedicated workflow, but legislation was redirected before that path. The direct `legislation discover/sync` handlers bypassed the file entirely. The scheduled workflow invokes the runner with checkpoint, terms and limit arguments. PyYAML 6.0.3 was locked transitively but not a declared direct dependency.

Final disposition is recorded in `evidence/migrations/corpus-legislation-nz/source-set-contract/inventory.json`. Both acquisition consumers now use the shared typed contract. The runner enforces lane, bound, checkpoint, exact inventory identity and preservation requirements. The direct CLI enforces activation, acquisition gate, active adapter, lane, bound, checkpoint and exact inventory identity. Generic capture handles typed adapters while retaining the explicit legislation redirect. Hugging Face, Zenodo, WARC, Parquet and external publication remain inactive.

Focused result after hosted patch-coverage repair: 126 passed; `archive_govt_nz.source_sets` reached 100% statement and branch coverage. Expanded isolated mutation result: 14/14 killed; receipt `/Volumes/PortableSSD/Quarantine/archive-govt-nz/source-set-11/mutation-reviewed.json`, source SHA-256 `2504be56411c5e57abc0dfa1186b755185c81be5e48c65508215e8ca4ef64f4e`.

Final native harness passed with four xdist workers: 4,318 tests, 97.43% repository coverage, schema 44/34, parity 9/9, all native mutation lanes, dependency audit, licence inventory, secret scan and 111-component SBOM. Validation receipt: `evidence/migrations/corpus-legislation-nz/source-set-contract/validation.json`. Actionlint reports only two unchanged base findings in unrelated workflows (SC2086 at global CKAN line 56 and scheduled Gazette line 36).
