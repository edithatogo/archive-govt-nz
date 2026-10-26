# Phase 3.2 dimension and mapping audit — 2026-10-26

This audit reconciles the source-literal assertion builders, their field links,
the cutoff-bound source census, and the existing mapping-contract evidence.
It records current support; it is not a crosswalk approval.

## Evidence-backed coverage

The Budget named-column expenditure profile carries literal vote,
appropriation, department, portfolio, amount-type and functional-classification
labels, an exact year token, the Amount $000 header, and its
appropriation_amount adapter measure. Its existing validation receipt says
all targets are unresolved and there is no economic-classification field in
that profile. The classification projection likewise retains the four
observed functional labels as unmapped source occurrences.

The CPI, annual-population, QES and GDP context builders carry source-linked
period tokens; the CPI/QES/GDP profiles also carry source-linked series,
measure and unit literals when present. The HAIR2024 fig27/fig28 adapter now
links exact source-column headers as measure literals and exact year tokens as
period literals. It emits no unit, denominator, price-base or currency mapping
because those qualifiers are absent or unverified.

The cutoff census binds the two HAIR2024 sources to
moh_vote_health-008 (c1e775…d48e9fc) and moh_vote_health-009
(7b9a51…b6266e4). It also records captured Stats NZ CPI, population, QES and
GDP objects and Budget 2026 expenditure (budget_2026-000,
3fc6bb…26f5a0). The census supplies resource identity and object digests,
not semantic crosswalks or effective-period decisions.

## Mapping decision

No retained source or mapping-evidence record establishes an approved target
identifier and effective period for the reviewed literals. Production mapping
target count remains zero. In particular, source labels do not identify
canonical vote, appropriation, department, portfolio or amount-type entities;
functional labels do not establish a separate classification scheme or
crosswalk; Amount $000 does not establish ISO currency; and fiscal/year
tokens do not supply approved start/end dates or a join policy. No economic
classification value occurs in the reviewed Budget profile.

Accordingly every emitted mapping remains unresolved, with a reason and a
source reference of the form sha256:<captured-object-digest>#<source-coordinate>.
The complete occurrence-level links remain available per fact. Assertion-level
references are deterministically sorted and capped at 32.

The shared contract now accepts a resolved target only with a method,
evidence-digest references, source references, and explicit inclusive start and
end dates. It validates structure only: it does not read or authenticate
evidence bytes, assign confidence, or confer approval. A synthetic positive
fixture verifies that shape without adding a production mapping.

## Remaining scope

This closes a contract and evidence-accounting increment, not the full Phase
3.2 mapping task. Economic-classification evidence, source-backed identifiers
and crosswalks, mapping adjudication/confidence, effective-period decisions,
remaining source-family dimension projections, and integrated drift/Gold
contracts remain open. Rights, currency, comparability and analytical joins
remain separate gates.
