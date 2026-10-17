# Vote Health capture cohort reconciliation — 17 October 2026

The original `source-census.json` is unchanged: 143 resources, 75 captured.
The new `capture-inventory-20261017.json` is a separately identified projection
of that snapshot, eight retained edition addenda and the existing 2018–2021
main Estimates request/capture cohort. It preserves 155 census observations
and 85 capture observations across 152 exact source URLs; 84 resources have a
recorded capture, including 68 Vote Health PDFs. Nine captured main Estimates
resources absent from the original aggregate are now accounted for; three
addenda corroborate existing resources rather than adding resources.

Every input is pinned by exact bytes, SHA-256 and logical filename. Grouping
uses exact URL, with all source IDs, observations and content versions retained.
Identical bytes at different URLs remain distinct resources. Discovery without
a hash and its later capture remain observations of the same URL. No current
state is inferred from conflicting or differently dated observations.

Nine capture observations verify the original capture-time request SHA-256,
source ID, URL and request-URL hash. The 2011/12 retained census itself matches
its capture-time request hash. The original 2009/10 and 2010/11 requests have
only `cutoff` and `records`; their exact original shape is retained. Seventy-six
legacy/corroborating observations lack the original resume request binding and
remain explicitly unverified for that binding. This is not proof that those
captures lack other provenance or that their originals are missing.

The two request/capture metadata files for four later editions are copied byte-for-byte under
`capture-cohorts-20261005/`; their existing native preflight is reused. No new
PDF preflight or recapture occurred. The builder accepts repeated `--census`,
`--capture-manifest` and original `--request` paths; `--output` is exclusive.
The committed rebuild contract assembles all named inputs without native data.

`capture-inventory-build-20261017.json` records two final byte-identical CLI
builds, unchanged inputs and the separate fixity receipt. Under the shared
validation guard, the native verifier freshly streamed SHA-256 and BLAKE3 for
all 84 captured URL/version identities (46,245,283 bytes), matched every
contributing capture result's size and available BLAKE3, and verified stable
file stat before/after. `capture-inventory-fixity-20261017.json` pins the exact
inventory and each verified object. The independent Conductor receipt review
confirmed exact set equality, counts, sizes and inventory pin without repeating
native reads. WARC payload/transport replay is outside this fixity receipt.

The inventory schema is part of the required repository schema harness.
Focused checks cover alias/revision preservation, distinct URLs with identical
bytes, request tampering, invalid source/digest/size, failed captures, malformed
censuses, original unversioned requests and exact retained-cohort rebuild.
The red phase failed because the module did not yet exist; final focused
inventory/source-health tests passed (66 tests). Ruff and strict typing pass.
The full frozen-tree harness and hosted checks remain required before merge.

This bounded cohort is not the complete source census: other contextual/donor
exports, remaining source families and publication variants still require
reconciliation. The separate 2019/20 Supplementary Addition remains eligible
for capture assessment. Neither capture coverage nor a copyright label admits
normalization, confirms redistribution rights, or establishes measure
comparability. GDP currency/denominator and other analytical gaps remain open.

Refs: #205, #207, #208, #211.


Redirect hardening preserves the requested URL as the resource identity and the
observed final URL in the untouched result row. Successful captures require the
original request-URL hash; failed captures retain their existing source-ID/URL
contract without a success-only hash. Distinct requests sharing a destination
remain distinct; missing, mismatched and ambiguous original bindings fail
closed. The actual retained cohort has no redirects, so its inventory bytes
and independent CAS fixity receipt remain unchanged.

The first frozen candidate passed the complete required harness (7747 tests,
10 skips, 97.41% coverage). Redirect/failure hardening is a subsequent candidate
and requires its own full assurance before PR delivery. Actual-cohort final
CLI builds remain byte-identical; no additional native CAS reads were needed.
