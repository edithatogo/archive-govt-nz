# Vote Health Supplementary Estimates category totals, 2009/10

Issue #211 now has an edition-specific Silver profile for the captured 2009/10
Supplementary Estimates PDF. The source census records Treasury's CC BY 4.0
notice and capture fixity. The profile is pinned to source SHA-256
`c6ed655b1dbca81b0fc54ef62547b71d5f984c6556cfdc77b6299c1bcc870a0e`.

The adapter emits only six printed category totals from pages 2–6:
departmental and non-departmental output expenses, non-departmental other
expenses, departmental and non-departmental capital expenditure, and total
annual and permanent appropriations. It retains the three `$000` budget
columns, source labels, parenthesized adjustments, direct field lineage, and
partial-page dispositions. Normalized-fact rights remain `not_evaluated`; no
cross-edition comparison, currency interpretation, Gold measure, federation,
or publication is asserted.

Persistent Silver and Bronze repeat-build results are recorded in the machine
evidence and clean-room recovery receipt linked from `index.md`. The source
PDF has a non-zero-indexed cross-reference table; pypdf corrected object IDs
while reading it, and the profile verified the source hash and extracted the
expected six labels. `./scripts/validate.sh` is required before a PR.
