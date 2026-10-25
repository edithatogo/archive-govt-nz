# Tobacco research source archive

The existing archive capture CLI owns HTTP retrieval, CAS and WARC. This profile
adds explicit sources and consumer bindings; it introduces no second storage
engine, scheduled job, scientific data model or automatic publication route.

## Coverage and reuse

`registry/tobac/sources.json` inventories 43 bibliography records from four
collections at tobac commit `59bb0e4ebaf1881158849df1702a1d3101aad58f`, grouped into
38 source identities by exact DOI or, where absent, exact URL. All original
collection/source-ID pairs remain intact. `consumer-inputs.json` inventories 18
CSV files, 326 rows, hashes and exact source-ID mappings. Internal references
`longitudinal_protocol` and `v2.6.0_parameter_estimates` remain unmapped.

The estate reconciliation records pinned Hugging Face repository revisions and
the public-web record-index hash. No exact URL matches were found in that index.
The legislation raw XML listing had no matching 2024/6 object. These checks do not
prove absence from compressed bundles, other datasets or the entire estate.
Existing exact objects should be reused only after revision, content hash and
source-edition verification, retaining both the upstream and consumer identities.

## Capture and postflight

Use the repo-local Python 3.15.1 locked environment. Choose a **new** run directory
for every acquisition; native WARC filenames are positional and would otherwise
overwrite a previous generation. Shared CAS objects are immutable.

```sh
uv sync --locked
.venv/bin/python --version
mkdir build/tobac/NEW-RUN
.venv/bin/archive-govt-nz capture --source-type tobac-sources \
  --store-root build/tobac/cas --warc-dir build/tobac/NEW-RUN/warc \
  --format json > build/tobac/NEW-RUN/capture.json
.venv/bin/archive-govt-nz capture --source-type tobac-pubmed-metadata \
  --store-root build/tobac/cas --warc-dir build/tobac/NEW-RUN/pubmed-warc \
  --format json > build/tobac/NEW-RUN/pubmed-capture.json
.venv/bin/archive-govt-nz capture --source-type tobac-source-assets \
  --store-root build/tobac/cas --warc-dir build/tobac/NEW-RUN/asset-warc \
  --format json > build/tobac/NEW-RUN/asset-capture.json
.venv/bin/python tools/verify_tobac_capture.py \
  --register registry/tobac/sources.json \
  --capture build/tobac/NEW-RUN/capture.json \
  --capture build/tobac/NEW-RUN/pubmed-capture.json \
  --capture build/tobac/NEW-RUN/asset-capture.json \
  --store build/tobac/cas --out build/tobac/NEW-RUN/bindings.json
.venv/bin/archive-govt-nz replay --cas-dir build/tobac/cas --format json
```

The native capture CLI returns zero for partial captures. Inspect every result;
zero exit status is **not** whole-source completion. The offline postflight checks
CAS fixity, WARC fixity, byte-for-byte payload agreement and request-URL identity.
It rejects duplicate URI receipts so callers must choose one generation explicitly.
The output file is created exclusively; previous bindings are never overwritten.
It emits an accounting of gaps, not a full-acquisition pass.

`tobac-pmc-supplement` is the three-URL first-run supplement discovered from the
NCBI XML article-ID list. Those URLs are already in `tobac-sources`; do not combine
both source sets on a later run. New PMID/DOI aliases must be reconciled in the
register and metadata source set together. Keep consumer bibliography hashes and
CSV mappings current, then run both repositories' archive-binding tests.

## First acquisition and limits

Native receipts and `capture-bindings-20261025.json` retain every attempt. The 12
Ministry of Health targets returned terminal HTTP failures (a sampled response was
403 with a Cloudflare challenge). PubMed HTML and Beehive returned challenge bodies,
including HTTP 200 responses. These are retained as failed/challenge evidence,
never accepted as original documents. NCBI's public EFetch endpoint supplied
bibliographic XML; five PMC article pages were acquired across the two runs.
ISPOR's shortened title did not pass the conservative identity screen and remains
unverified rather than being silently accepted.

`metadata_only` is not full text. `source_html_identity_observed` is only an HTML
title identity screen: tables, supplementary files, numerical extraction, licences
and complete-document coverage still require review. Source identity is not
independent evidence; Phyo/MOH/NZHS and Wang-derived inputs retain shared-data
dependencies. Current redirects do not recreate the agent's historical edition.

The native WARC writer did not record `WARC-Date`; bindings preserve null instead
of inventing exact capture timestamps. The acquisition run is dated 25 October
2026. WARC fixity is verified, but full WARC conformance is not claimed. Future
writer hardening should preserve originals and produce a new generation.

Raw responses are stored outside Git and retained in the canonical local archive
at `build/tobac-source-archive-20261025/`, including CAS and all four WARC runs.
Tracked receipts contain metadata and hashes only. Hugging Face collections are
discovery views; this task does not create a new dataset, change estate taxonomy,
or upload response bodies whose source-specific redistribution terms remain open.
The scientific consumer keeps its extracted values and assumptions unchanged.

## Recovery

Retain the canonical local directory before removing the implementation worktree.
Run the archive's native CAS replay and each WARC manifest verification against the
retained copy. To repeat postflight there, copy the register and native receipts,
preserve their `build/tobac/...` relative layout or explicitly adjust a derived
receipt with provenance, and pass the corresponding `--root`. Do not edit the
original receipt. Remote or second-device recovery remains unqualified until a
rights-appropriate destination has a verified copy of the actual objects.

The original tobacco-volume XLSX is an important exception to the blocked landing
pages: its directly published file URL was accessible. Native capture preserved
its original bytes and WARC; `workbook-reconciliation-20261025.json` records all 16
year/value pairs matching the consumer CSV exactly. The source register includes
the expected header, row values and consumer hash. The postflight compares these
with openpyxl and emits `source_workbook_values_matched` only for an exact table
match. This closes transcription parity for the current workbook snapshot; it
does not resolve the existing product conversion or domestic/duty-free questions.
Two additional supporting agent notes are inventoried without being relabelled
as original documents. Current coverage is 10 HTML source identities, one verified
workbook identity, 14 metadata-only identities and 13 unresolved identities.
