# Implementation plan

Status: deferred. Completed bounded fixture tasks remain recorded below, but
no incomplete task is authorized to resume until the registry deferral gate is
satisfied with corpus and workload evidence.

- [x] Create fixture manifest and immutable fixture hashes.
- [x] Build minimal RO-Crate metadata package and validate JSON-LD shape.
- [x] Build BagIt package and verify payload manifest and tag manifest closure.
- [x] Build OCFL object/layout fixture and validate required inventory/version links.
- [x] Run available reference validators; record unavailable tools without substituting claims.
- [x] Test extraction, checksum closure, provenance linkage, and deterministic reruns.
- [x] Compare results and publish an adoption recommendation with explicit limits.
- [x] Update the track and GitHub issue hierarchy only from receipts.
