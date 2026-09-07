# Dated correction: P2.11 pacing and assessment guards

2026-09-07, P2.13. Independent reviewer findings are confirmed. This correction
supersedes the blanket pacing-compliance statement in
`candidate-cohort-review-20260907.md`; that historical report and every recorded
observation remain byte-identical. See the paired JSON for exact hashes/time.

## Confirmed historical breach

Italy (`it-government-portal`) recorded `Crawl-delay: 10`. Its root request began
at `2026-09-07T02:50:01.291537+00:00`; its redirected `/it` request began at
`2026-09-07T02:50:02.307348+00:00`: **1.015811 seconds**, not ten seconds.
The earlier collector slept the robots delay once but paced redirects using only
the one-second default. Thus the earlier statement that crawl delays were
respected is false. The metadata remains an observation, not compliant-acquisition
certification. No cohort was replayed and no historical bytes were rewritten.

`candidate-probe-acquisition-20260907.py.txt` retains the exact historical
collector bytes identified by the original input's `collector_sha256`. The
identity test now verifies that immutable snapshot rather than incorrectly
requiring corrected current code to hash to the historical collector.

## Corrections and regression evidence

1. Store the strongest learned crawl delay per normalized origin and apply
   `max(origin_interval, learned_delay, applicable_delay)` **inside its lock on
   every hop**. Same-site redirects and later callers without a fresh policy
   share the same spacing. Remove the one-off sleep. Virtual-clock tests cover
   crawl-delay five versus interval one and the inverse, canonical-host
   redirects, and a subsequent request without its own policy. Existing source
   and cohort timeouts still bound waiting. Policy cannot be applied before it
   has been learned; this patch makes no claim of historical compliance.
2. Bind page media type and outcome to the terminal trace. Observed success
   requires 200 HTML/XHTML with existing digest/byte checks. Only observed
   `text/plain` converts to `non_html_metadata`, with empty title/navigation.
   Preserve all failure outcomes. A mutation of the **actual retained AE 404**
   to aggregate/page `observed` plus catalogue title/link is now rejected.
   Media substitution, false conversion and failure swapping are also rejected.
3. Reject NaN/infinity, strings, nulls and booleans in every duration including
   origin spacing. Counts require actual integers (not booleans), with at most
   eight workers, one million page bytes and three redirects; positive request,
   source and cohort times and nonnegative spacing remain required.

Red phase: six of eight new pacing/terminal checks failed as expected; forty of
52 budget checks exposed accepted invalid values or wrong exception classes.
Green phase: **208 focused tests pass**, including all historical golden reports.
Ruff, format and scoped BasedPyright pass. Combined changed-module line/branch
coverage is 87% (probe 83%, cohort 95%); no full-harness or complete-module coverage
claim. Commands are recorded in `runlog.md`. Tests exercise all added executable
lines and the new outcome/conversion branches. Mutation regressions operate on
temporary copies of evidence, not the retained originals.

## Delivery boundary

These repository-owned fixes resolve the three identified guard defects, not
the historical acquisition breach. Full integration remains with parent.
No rights decisions, publication, schedules, global registry changes, remote
writes or network reads were performed during the correction. The six linked
observations were taken before this priority request and remain separately
held for P2.12 review; they are not a run under the corrected collector.
Parent must integrate this fix before further cohort delivery and preserve its
accepted P2.5–P2.8 statuses. P2.2/P2.3 broader acceptance remains open.
