# Residual6 packaging completion — 2026-09-07

Follows BEFU86 commit ee8da4e2bf46d8a9bd6198cc5598581012dd29ed in the
isolated HYEFU16 worker. Conductor implement/review used with dedicated evidence
and focused validation only. Phase4.2/M-07, AC-03/05 bounded persistence.

New packaging profiles befu-residual and hyefu-residual invoke only existing
hash-bound admissions. The adapter exposes its already-computed inventory.
No new selectors, parser, source, capture, period interpretation or arithmetic.
Each selected cell has a native record plus field references; each sheet has
an exact preserved-only remainder. No formula-exclusion records are invented.

BEFU Data 2.12 C8 remains one Health net-capital observation with unknown period,
null bounds, and seven native references. HYEFU Table 2.10 D14:H14 remains five
OBEGALx-movement observations, not spending, with four Forecast columns and a
distinct Total/change column, null projected bounds, and 80 native references.
Both preserve null currency, exact decimal tokens, source headers, labels,
number formats and all native context. The 87 native references are distinct
from additional generic context-lineage rows in the shared physical package.

Strict verification covers selected coordinate sets, native lineage, source
anchors, measure, label/unit/header meaning, unknown period bounds/status,
identity, nested/envelope equality and existing fixity/area contracts.

## Validation

- TDD red: all 24 new cases failed on unsupported profile before implementation.
- Focused affected suite: 267 passed across residual/chart/allowance package
  and admission tests, literal package/coverage tests, rebuild and rebuild_eight.
- Coverage: residual adapter 47 statements/4 branches; writer 83/30; verifier
  158/44. All 100%, no coverage exclusions.
- Cold unfiltered mutants targeting those three modules: 235/235 killed,
  zero cache hits, 176 baseline tests passed. Options: --gremlins
  --gremlin-clear-cache --gremlin-no-coverage-filter --gremlin-workers=4.
- Ruff check/format, basedpyright and git diff whitespace checks passed.
- Commands used PYTHONPATH=src and archive-govt-nz/.venv/bin/python.
- Self-review: no orchestration v1/v2, resume, CLI, Gold, rights, original-byte
  or parent changes. No full harness, publication or lifecycle closure claim.

## Retained replay and regressions

Existing chart-packages replay.py was called with each exact retained admission.
It independently resolved XML numeric cells, compared every native record field,
amount and native reference, and compared all four files across two fresh builds.
No source bytes changed. Caller-supplied donor observation context is not a new
HTTP observation attestation. Rights remain not_evaluated; promotion not_performed.

Output root:
/var/folders/m9/_g3wndrn04d80ys2382r700r0000gn/T/health-residual6-sfrpcfwd

| Profile/file | SHA256 |
| --- | --- |
| befu-residual/MANIFEST.json | 888e1d70d48866a579c7c57b99f674601002ebf1dff14914efca8a00e9d3f930 |
| befu-residual/literal_facts.parquet | b2c3cd26c7f8e73cfb5a8edf747e0c387da3c5e73346ff884ee0b6876cf366cb |
| befu-residual/field_lineage.parquet | 8f35c94e3549af49a6c67b9a16ed04ea76f11bff3d40c1c31b2ff64e227ff985 |
| befu-residual/area_dispositions.parquet | e663afad8745e4c106605aa3bde8e36dca4245f9baa8554ac81cb7091b3fc279 |
| hyefu-residual/MANIFEST.json | bbedd633a5283fb29409b334196e161bd068839cb5ccb029d2eaf6af6216cc40 |
| hyefu-residual/literal_facts.parquet | 620e6462dc122c4dbfa4e3bdcd13594fa7e873d5f6a1adcea1962a9f3d0da316 |
| hyefu-residual/field_lineage.parquet | efdb4e67798c8a17413ee008d25c0d02a08e6974afed1ae0ae4a06142c69448e |
| hyefu-residual/area_dispositions.parquet | 41aa998414cbf4687d0c0c1acbb9994f559a296f550c5c866ff9738c82e74ec4 |

Two additional HYEFU16 and BEFU86 regression builds under
/var/folders/m9/_g3wndrn04d80ys2382r700r0000gn/T/health-chart-regression-jegp42_b
matched all previous four-file hashes, including both MANIFEST.json hashes.
HYEFU16 compared to its committed replay.json; BEFU86 compared to the retained
prior first build whose hashes are recorded in befu86.md.

The chart packaging batch is complete within this exact scope; other chart
areas, whole-donor coverage, source rights and integrated acceptance remain
separate. No further feature started.
