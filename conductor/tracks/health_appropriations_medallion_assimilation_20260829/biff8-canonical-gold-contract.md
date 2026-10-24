# Budget2019 BIFF8 canonical and Gold integration

Implements M-05/06/07/10/11/13/16. PR732 delivered source-native Silver;
its merge is 169fd175707b5d3424e4407201ba5678ea072684. The producer
checkpoints and qualification receipts remain immutable.

Canonical v3 adds explicit value basis, canonical stored integer and numeric
witness references to appropriation/revenue facts and field lineage. Existing
v1/v2 shapes and OOXML token consumers remain unchanged. Numeric evidence is
retained verbatim in its companion table, including source/stream/record/cell
identity and encoded bytes. Numeric fields never impersonate source text.

Admission binds a caller-pinned Silver manifest, closed four-table inventory,
exact typed snapshots and metadata to a complete replay from the hash-bound
Bronze original under the trusted edition profile. Canonical readback replays
this path again and compares every output and marker. All source lineage and
row dispositions remain available through pinned Silver; every selected field
and definition link is projected, with explicit target IDs and witness refs.
Gold uses existing exclusive export and named-query architecture, retaining
individual source-separated rows and witnesses. No parent/category sums,
netting, temporal alignment, deflation or cross-source comparisons are admitted.
Rights, currency and period-start holds remain unchanged. Repeat builds must
have identical bytes. Corruption, missing/extra rows or witness references and
unsupported profiles fail closed. Original full harness and three-platform
required checks precede protected delivery; 80 percent coverage floor unchanged.

The canonical marker retains the exact original caller observation-time token;
Silver metadata normalizes the timestamp, but its observation identity hashes
the caller token. It remains caller context, not evidence of capture. Replays
use that pinned token. Source decimal precision/scale stay null because binary
stored integers do not evidence a decimal lexical precision. Period labels are
explicit renderings of replayed year integers; year witnesses remain in lineage.
Gold emits no BIFF8 plot or cross-profile revision claim while parent/category
series comparability remains unqualified; the product report records both holds.

Gold manifests inline numeric cell/witness lookups and refer to the hashed
full-lineage companion by canonical lineage ID. All text/definition/numeric
links remain in that companion without truncation. This avoids duplicating
all source text lineage into the capped manifest. The cap remains4MiB.

The v3 registry is closed to appropriation_fact, revenue_fact and field_lineage;
other recordsets retain v1/v2 only. Independent codec/transport representation
changes may be accepted only after bounded typed readback and full replay equality.
The existing revenue fixture exercises dictionary-free Zstandard Silver snapshots
without adding a parallel test framework or pursuing coverage above the80percent floor.
