# Medallion backfill and replay vocabulary v3

Version 3 adds deterministic backfill and replay semantics without changing
immutable v1 or v2. Logical partitions are distinct from immutable snapshots.
Repeated observations are idempotent, late arrivals append to their partition,
corrections create a new snapshot with an explicit predecessor, and missing
payloads remain metadata-only and ineligible for replay.
