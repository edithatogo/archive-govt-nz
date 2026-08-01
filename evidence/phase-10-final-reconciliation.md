# Final evidence reconciliation

Status: **reconciled**

| Stage | Count |
|---|---:|
| discovered | 91 |
| resolved | 91 |
| captured | 12 |
| restricted | 78 |
| unavailable | 1 |
| tombstones | 79 |

## Checks

- `discovery_resolution_ids_match`: PASS
- `tombstones_match_unresolved`: PASS
- `resource_count`: PASS
- `capture_summary_closure`: PASS
- `release_reconciled`: PASS

Live payload and WARC completeness remain explicitly gated; no external request was sent.
