# Delivery scope and roadmap

User direction, 29 October 2026: simplify implementation and finish a usable
baseline. This document sets the current delivery boundary and supersedes
open-ended progression through historical programmes. It does not mark unfinished
corpora complete or cancel another owner's in-flight operation.

## Finish now: usable archival software

The baseline is a locked Python 3.15.1 package with working CLI entry points,
bounded configured capture, immutable originals and provenance, WARC/fixity
verification, local replay, and explicit failure/rights handling. Existing domain
implementations remain available. Completion is not conditional on acquiring
all historical records or implementing every research product.

This delivery's remaining work is finite:

- Simplify the routine workflow and remove automatic backlog expansion.
- Provide PR/release assurance profiles without reducing full-suite coverage,
  integrity checks or security requirements.
- Verify clean installation, CLI startup, local preservation/replay behaviour,
  and the complete release assurance profile once at the integration milestone.
- Deliver the reviewed source change through required hosted checks.

Acceptance: these checks pass and the delivered revision is identified. Source
coverage and live service outcomes are reported separately. Results belong in
the registry's existing coordination entry and the PR, not a new document pack.

## Later work

These remain worthwhile but do not block the software baseline. Historical
requirements and receipts stay intact; unchecked historical tasks are not waived
or presented as passed. Select an item explicitly before starting new expansion.

| Item | Existing reference | Resume when |
| --- | --- | --- |
| Health historical source census and additional workbook/year bridges | Issues #205, #207–#209, #211; Health appropriation track | A defined source/year cohort is needed for a user deliverable |
| Additional Gold, context, longitudinal and research products | Issues #211–#212; Health appropriation track | A concrete analytical question and accepted source cohort are selected |
| Broader Health publication candidate and corpus recovery | Issue #215 | A specific publication package and its source rights are ready |
| Global FOI country expansion and orchestration takeover | Issues #234–#241; global FOI track | One bounded country/source and transfer scope are selected; preserve the existing donor until then |
| Parliament historical backfill, additional collections and final coverage reconciliation | Issues #778, #782–#783 | A bounded historical interval or collection is selected |
| Broader MCP standards work, indexing, vector/graph products and further preservation-format conformance | README and existing archived architecture tracks | An identified consumer requires the capability |
| Gremlins campaigns, profiling and additional assurance infrastructure | Existing `--include-heavy` lanes | A concrete performance, integrity or release question justifies the run |

Previously implemented features stay available. Do not rewrite historical track
metadata just to make the programme appear finished, or open a fresh issue for
each row. Existing issues are the backlog references.

## Operational follow-through, separate from implementation

- Parliament's existing track records a retained HF 429/checkpoint recovery and
  paused continuation. Its native owner must reconcile current receipts and
  authority before any resume; this source-only delivery does not retry writes,
  enable schedules or claim recurring operation. See issue #794 and the P7 run log.
- Open PR #828 concerns retained-capture orphan recovery; #776 concerns tobac
  provenance. Their existing owners retain delivery. They are not absorbed into
  this change. Dependabot #777 is ordinary maintenance.
- Natural schedule evidence, exact publication readback, rights decisions and
  external recovery are accepted against their actual source/manifest. A green
  software build does not complete these operations.

Do not stop or relaunch another lane to apply this roadmap. At its safe terminal
checkpoint it can retain evidence and place any unselected expansion here.

## Working cadence

Bootstrap with `uv sync --locked`; verify `.venv/bin/python --version`. Use the
existing [focused test helpers](testing-profiles.md) while editing. Run the PR
harness once per reviewable candidate and the release profile at integration.
Reuse successful unchanged stages. The ordinary PR profile has 13 stages;
the release profile preserves all 32. Linux CI supplies release assurance once,
while macOS/Windows exercise the same full suite and coverage in the PR profile.

One concise record, one coherent PR, one self-review, required checks, delivery.
No routine permission question or automatic next-track creation follows success.
