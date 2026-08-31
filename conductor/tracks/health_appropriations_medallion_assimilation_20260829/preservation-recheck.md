# Independent local preservation recheck

Observed2026-08-31T15:29Z. This read-only audit used streaming SHA-256 and
byte counts, then parsed each WARC response and checked its payload against
the captured CAS identity. It did not rerun extraction, contact sources or
Hugging Face, qualify rights, alter originals, or approve a candidate.

| Scope | Entries verified | Bytes verified |
| --- | ---: | ---: |
| Complete-capture CAS originals |73|38,877,606|
| Complete-capture WARC receipts |73|38,915,034|
| Donor manifest objects |23|6,604,301|
| Listed v4candidate files |94|39,390,246|

These are overlapping collections, not additive unique-byte totals. All73WARC
files contain exactly one response; each decoded payload has the same SHA-256
and length as its captured original. There were no missing or mismatched
objects. The94candidate entries exclude the root candidate manifest itself,
whose independent pinned digest was also verified.

Pinned complete-capture manifest:
`04145e4030bfddaecade1af542e12cb8a56a187c9c924b7a4c135537ccae9dab`.
Pinned v4candidate manifest:
`9a33babda857b0aa7c60a6012000cf1e730fed729781cb8ceb6e7a4714cae40e`.
Observed donor manifest:
`893f387e1f361400285ccc84802b497e87802d1ad913826ff7d9055b07a03b74`;
this audit checked its internal file count, total size and object identities,
but did not independently pin the donor manifest from Git or reconstruct the
donor Git tree. The donor's prior pinned snapshot evidence remains separate.

Local audit script SHA-256:
`a364465d8191795d427c8e7e5ec3bbba647c626e52bfb73db8570b68862fc335`.
The script is retained outside Git at
`/tmp/health-compatibility.qDiHHO/preservation-audit.py`. Its output contains
aggregate evidence only; no original payloads or source metadata are committed.

This does not establish complete historical coverage, semantic validity of
every source, future disk state, or the current state of remote HF bytes. New
source-specific and canonical derivatives are not implicitly included in the
older v4candidate or its publication approval.

## Separate donor Git identity check

A subsequent read-only check recomputed all23Git blob identities directly from
the retained CAS bytes, then assembled Git tree encodings from the recorded
paths and modes. The resulting tree matched the independently recorded donor
baseline `c6d44ff79eda73cfc6ba7db5764e27ce01b890e1`. This establishes the retained
snapshot's path/mode/blob/tree identity; it does not reconstruct Git commit
history or change the earlier manifest-audit scope. Script SHA-256:
`c114e7fd23eb8b1a577edd3ef182b23fe2ae829861520930dd8e0238d2121fea`,
retained at `/tmp/health-compatibility.qDiHHO/donor-tree-audit.py`.

## Repository assurance

The docs-only reconciliation checkpoint `063a324` passed
`COVERAGE_CORE=ctrace PYTHON_JIT=0 PYTEST_XDIST_AUTO_NUM_WORKERS=4 ./scripts/validate.sh`
with exit0:2,972tests/eight warnings,68.99seconds,97.11%coverage;74Conductor
tracks,41schemas/31samples,9/9parity, all mutation/security/supply-chain gates
and111SBOM components. CAS throughput467.62MB/s. Full log SHA-256:
`f39aeedd4d55b36fffc2888112c30666f9002762d9e613477e29f992f5af5173`.
The donor-tree addendum and this result receipt were appended after that run;
they are not a claim of another full native invocation. Two owned generated
timestamp-only fixture diffs were restored after the harness exited.
The first post-run ledger validation rejected two new result events missing
their required observation timestamps. Those receipt fields were added; no
production or source data changed, and the invalid intermediate events were
not committed or presented as valid evidence.
The later merge of main `0a076fa` retained the full incoming80-event ledger
prefix plus three unique audit/result events. The existing append-only ledger
conflict was resolved without rewriting any earlier event; Conductor validated
all75tracks afterward. The original native result remains bound to `063a324`,
not relabelled as a full run of this later integration.
The subsequent optional Health Survey assessment is a documentation-only
addition based on primary public landing pages; its75-track Conductor check,
secret scan and whitespace check passed. No survey payload was acquired and
the earlier full harness is not relabelled as validation of a survey adapter.
