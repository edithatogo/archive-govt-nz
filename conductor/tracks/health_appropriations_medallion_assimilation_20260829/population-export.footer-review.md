# Population footer review correction

Banach's P2 finding is confirmed: the initial validator checked required
marker presence but ignored arbitrary additional single-column footer rows.
Appending contradictory status/unit/base notes could pass.

Five additive red regressions reproduced this defect. The corrected validator
requires the complete ordered reviewed footer, including revision notes, symbol
definitions, status visibility and contact lines. Only the observed empty and
single-space separators are ignored. New notes require explicit profile review;
they cannot be silently treated as irrelevant prose.

Focused population export/context suites: 54 passed, 100% of 79 statements
and 10 branches. Ruff, formatting and strict types pass. Reordering, omission,
extra columns, duplicate markers and additive notes are covered. The synthetic
positive fixture now represents the full reviewed footer with invented amounts.

Evidence boundary: the earlier live CSV response bytes were **not retained**.
The source digests and observations in population-export.validation.json are
historical author observations, not independently replayable payload evidence.
This correction was tested against synthetic bytes and the reviewed response
transcript; it does not independently replay or revalidate those original live
responses. A future capture-owner operation must retain the actual bytes and
HTTP evidence before independent replay can be claimed.

No fresh network request, capture, publication or analytical decision occurred
for this fix. The CPI/QES expansion test remains separate and unstaged.
