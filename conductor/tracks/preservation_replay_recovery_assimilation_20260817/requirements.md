# Track 6 Requirements (MoSCoW)

## Must Have
- **MUST-1**: Produce ISO 28500 compliant WARC record files containing `warcinfo`, `request`, `response`, and `metadata` records.
- **MUST-2**: Convert donor historical flat archives into SHA-256 CAS objects with complete fixity receipts.
- **MUST-3**: Implement offline deterministic replay engine to verify that archived raw byte streams can reconstruct original parse trees.
- **MUST-4**: Implement automated restore rehearsal tool testing complete recovery from published snapshots.

## Should Have
- **SHOULD-1**: Support WACZ packaging for browser-based interactive playback.
- **SHOULD-2**: Support rolling archive compaction to prune redundant intermediate payloads.

## Won't Have
- **WONT-1**: Do not discard any historical raw captures during compaction.
