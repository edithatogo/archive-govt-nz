# P2.11 complete factual candidate cohort

## Acceptance and actual observations

All remaining 223 URLs now have a source-bound, dated factual assessment.
The earlier AL/BH assessments are copied unchanged into the 225-source report.
This completes this bounded assessment cohort, not whole P2.2/P2.3, exhaustive
country discovery, adapter qualification, catalogue publication or capture.

Acquisition ran 2026-09-07 02:48:50–02:51:44 UTC: 380 completed HTTP observations,
15,724,022 recorded response-body bytes, no retries. A cancelled request may
have transferred bytes not present in completed-response counters. All 223
candidates started within the cohort deadline; none was omitted or deferred.
There are 106 observed HTML responses, eight HTTP errors, 96 robots-unverified,
one robots-disallowed, three byte limits, three request timeouts, four cross-site
redirects not followed, one unsafe redirect and one source timeout. A successful
challenge response remains access-unverified. HTTP responses establish an
endpoint, not official publisher attribution or a functioning FOI catalogue.

New interface dispositions: eight out-of-scope-for-FOI-capture general data
catalogues; four FOI navigation leads; 93 FOI-scope-unverified; 118
access-unverified. BH's earlier general catalogue evidence is preserved separately.
Out-of-scope means the observed general catalogue interface, not that the entire
institution/site/country lacks FOI disclosures. The title-plus-catalogue-navigation
rule is deliberately conservative for multilingual and JavaScript-only sites.
No absent link is treated as exhaustive discovery. AL year-register links remain
a bounded follow-up lead, not a basis to claim requests were enumerated here.

## Guard and reproducibility

`foi_candidate_probe.py` reuses the capture URL guard and adds public DNS
validation with connection address pinning and original TLS SNI/Host. Each
request has an isolated client: no credentials, cookies, environment proxies,
automatic redirects or retries. HTTPS only, no query strings/fragments,
non-public addresses, private redirects or cross-site redirect following.
Robots is checked first; 404/410 means absent for this observation, not permission
to publish. Unverifiable robots stops homepage observation. Applicable disallow
and crawl delay are respected; same-site redirect destinations are rechecked.

Bounds: eight workers, ten seconds/request, forty seconds/source, 1,500 seconds
for the cohort, three redirects per chain, one second/origin, 65,536 robot bytes
and 1,000,000 page bytes. Identity encoding only. Body memory is capped; streaming
limit detection can receive one additional 16,384-byte chunk. These are response
body bounds, not TLS/header/wire-byte accounting. At most eight HTTP observations
per source (two chains of four), with no discovered-link fan-out. No raw body is
retained: only digests, counts, dates, transport outcomes and bounded title/known
navigation metadata. DNS/TLS errors are sanitized, not misrepresented as 404.

The immutable observation input pins baseline bytes and exact collector bytes.
`foi_candidate_cohort.py` performs offline identity/cohort, date, trace, robots
admission, byte/hash-shape and metadata validation. It preserves prior restrictive
dispositions and policy fields; hashes attest the observation record, not replayable
original page bodies. JSON and Markdown are deterministic and covered by golden
tests. Reproduce offline with `PYTHONPATH=src python -m
archive_govt_nz.foi_candidate_cohort` followed by the track's
`candidate-assessment.json` and `candidate-observations-remaining-20260907.json`.
For a future explicitly authorized new observation, `collect_file(baseline_path)`
returns a new dated input; do not overwrite these historical observations.

## Review and validation

148 focused tests pass: candidate probe/cohort/assessment, reconciliation,
catalogue, discovery, rollout and evidence verification. Changed-module combined
line/branch coverage is 86% (probe 81%, cohort 95%); this is not full harness
certification. Ruff and scoped BasedPyright pass. Tests reject omitted/duplicate
or substituted candidates, mismatched hashes/dates/bytes/navigation, and check
DNS pinning, private targets, robots refusal, cross-site redirects, compression,
streaming caps, concurrency/deadlines, privacy filtering and unchanged policies.
Conductor implement/review guidance informed acceptance-linked records and scoped
review; user delegates the full integration harness to parent.

## Remaining work and external inputs

No external input or human approval is needed to finish this factual cohort.
Failures are completed observations with unresolved facts, not a human queue.
Next safe slice: bounded metadata inspection of the four FOI leads (GG, JM, KY,
UM) and AL linked year registers, recording source-specific scope and adapter
evidence. For each failed URL, later progress requires an actual successful
public response/robots observation or a separately evidenced replacement URL;
the exact URLs, dates and failure classes are in the retained input. Do not retry
disallowed targets or bypass access controls. General catalogue interfaces do
not need a FOI-capture approval queue.

Rights owner policy is unchanged: institutional explicit licence plus nonpersonal
schema evidence and mixed correspondence metadata-only remain distinct. No rights
decision, schedule, raw eligibility, publication, remote write or global registry
change was performed. P2.2/P2.3 remain open for their broader requirements.
Parent integration must preserve accepted P2.5–P2.8 statuses and rechain only the
new ledger append against its advanced ledger; this plan patch is additive P2.11.
