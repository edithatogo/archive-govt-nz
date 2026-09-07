# Guarded linked cohort and AL year-index adapter contract

P2.15, 2026-09-07. Separate next-delivery worktree, based on guard commit
`9ed5f491fb11a952f85e8c8b19aceece88ce3617`. The frozen delivery worktree is
untouched. This completes bounded factual navigation assessment, not broader
P2.2/P2.3, record acquisition, rights clearance, schedules or publication.

## Retained guarded cohort

[Machine assessment](linked-foi-assessment.json), [human assessment](linked-foi-assessment.md),
[observations](linked-foi-observations-20260907.json), and
[provenance](linked-foi-provenance-20260907.json) retain the completed corrected-
collector read at 03:55:17.146021–03:55:29.850844 UTC without another cohort replay.

| Target | Guarded outcome | Factual disposition |
| --- | --- | --- |
| AL 2026 | observed | Register-table interface; no request denominator |
| AL 2015–2025 | observed | Older register landing; navigation assessed below |
| JM | observed | Access-to-information information page |
| KY | observed | FOI information page |
| GG | timeout | Access unverified; no success inferred from its earlier homepage |
| UM | robots_unsupported_rules | Blocked before page access; no bypass |

UM's recorded robots policy has `allowed: null` and no page/redirect request.
The guard conservatively rejects complex path rules; this is an unsupported
interpretation disposition, not a determination that the source owner prohibits
all access. The earlier pre-fix DOI page observation is retained unchanged and
does not override the newer blocked outcome. No human factual-review queue.

Eleven completed trace entries record 833,875 received body bytes. Counts are
retained response-body counters, not TLS/header wire accounting or omitted
partial timeout traffic. Configured bounds remain eight workers, ten seconds per
request, forty per source, 1,500 per cohort, one million page bytes, 65,536 robot
bytes, three redirects and per-origin pacing. The corrected guard/delay checks
were used; this is not a general robots-compliance certification. No full
223-source replay, API, attachment or correspondence retrieval occurred.

## AL older index: observed scope

A single additional guarded index read ran 03:59:06.875225–03:59:10.444424 UTC:
robots then the already-evidenced 2015–2025 index, no link fan-out. Robots returned
107 bytes; the HTML returned 258,719 bytes. The HTML SHA-256 matches the earlier
index observation, but this read has its own date and transport evidence.
See [navigation observations](al-year-navigation-observations.json) and
[validated adapter contract](al-year-navigation-assessment.json).

The page yielded **ten same-site register links**, labelled 2015–2016 jointly and
2017 through 2025 individually. Eleven year labels are observed. This is the
selected navigation on one page, not exhaustive historical discovery or annual
record coverage. One embedded-resource element was counted; its address and
contents were not retained or followed. No case text, arbitrary labels,
correspondent names, attachment contents or embed URLs were exported.

## Reusable adapter contract

`foi_year_navigation.py` provides a finite-vocabulary parser and offline validator.
It accepts bounded year labels in the 2015–2025 scope, retains safe same-site
register URLs only, deduplicates and caps navigation at 32 links, and never
follows them. It uses the existing safe transport and cohort collector; no
parallel transport implementation or changes to current-batch modules were made.

The accepted entrypoint contract is `html_year_link_index`. Subsequent work must
first observe a selected linked resource's actual media type under the same
guard, then qualify an appropriate format-specific parser. URL spelling does not
establish MIME type or content. `linked_resource_media_types` remains
`not_observed`; record parser, capture adapter and automatic following are false;
request denominator remains null. No implicit adapter activation is performed.

The validator binds source identity and terminal transport, checks every retained
navigation structure including failure/robots metadata, rejects unsafe links,
unexpected fields, duplicate links, invalid years/counts and changed page/trace
metadata. The exact supported AL entrypoint is checked. Input digests and prior
source-page identity remain separately inspectable. No derivative reconstructs
or substitutes for original HTML preservation.

## Focused validation and review

Initial parser test was red for the missing module, then green. Final focused
suite: **269 tests passed**; new module **100% line and branch coverage**. Ruff,
format, scoped BasedPyright and track checks pass. The guarded cohort's generated
JSON/Markdown reproduce through the existing assessor; the AL contract reproduces
exactly from its retained observation. Preservation tests bind historical files
and the rights-owner record without rewriting them. Conductor implement/review
guidance informed scoped acceptance and negative-path checks. Python/general
guides apply; no new dependency, platform integration or global registry change.

The parent owns the full integration harness. On integration preserve accepted
P2.5–P2.8 status changes and rechain only new ledger appends against parent history.
No frozen delivery files, rights/publication policy or existing collector source
were modified. Only the isolated next-delivery source/test/FOI track paths change.

## Remaining factual work

No external input is required to accept this bounded navigation contract. A next
safe cohort could qualify the combined 2015–2016 and newest 2025 linked interfaces
as representative resource formats, retaining failures without a bypass. Until
then, annual resource types and record parsers are unverified. GG remains timed
out; UM remains blocked by unsupported rules. Neither needs a human factual-review
queue. Institutional licence/nonpersonal-schema and mixed-correspondence
metadata-only boundaries remain unchanged; publication requires separate evidence
and authority.
