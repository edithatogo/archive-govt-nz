# Verified CPI source-health profile

`build_report(..., cpi_evidence=CPIEvidence(cas_root, warc_root))` regenerates
the existing closed CPI source-evidence profile and verifies its independently
fixed0716432e report digest. Supplied census bytes must match decoded inputs;
source ID, body digest, URL, historical observation, series, unit and vintage
are checked before adoption. Only explicit evidence produces source-health v2.
Default v1 JSON and Markdown remain unchanged for the same inputs.

The new report retains the seven body/WARC descriptors and reports449 represented
quarter labels,422 numeric and27 publisherNA. It does not assert numeric
continuity, freshness, fiscal alignment, rights or analytical admission. Other
context and resource states remain unchanged. Observation timestamps do not
become source vintages.

The existing `tools/build_health_source_health_report.py` accepts paired
`--cpi-cas-root` and `--cpi-warc-root` with explicit distinct `--json-output` and
`--markdown-output` paths. Body roots use SHA256-prefix directories; WARC roots
use flat digest filenames. Historical default outputs are protected, and an
existing different output is refused; identical replays are supported.

The schema is `health-source-health-report-v2.schema.json`; it pins the bounded
CPI proof, while retaining the existing whole-census report structure. The
representative fixture is a reduced one-source/one-context schema sample, not
a completeness claim.

Focused contracts:69passed; Ruff/typing/Conductor validation pass;66schemas and
56 representative documents validate. Initial missing API collection failure and
a counterfeit-test failure caused by a cached imported verifier alias are
retained externally; dynamic module lookup restores correct scoped verification.
Actual-source offline repeat and full/hosted assurance remain pending under the
coordinator's launch ownership. The wider track remains open.

Native1 found that an existing destination was selected as prior-report input.
V2 now defaults independently to the retained historical baseline unless
`--recorded-report` is explicit. V1 input-selection semantics remain unchanged.
The sentinel was preserved;70focused checks pass after correction. The failed
first proof and partial artifacts remain separate from the fresh native2 replay.
