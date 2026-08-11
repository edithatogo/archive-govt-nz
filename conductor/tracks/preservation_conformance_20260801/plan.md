# Implementation plan

1. [x] Create fixture manifest and immutable fixture hashes.
2. [x] Build minimal RO-Crate metadata package and validate JSON-LD shape.
3. [x] Build BagIt package and verify payload manifest and tag manifest closure.
4. [x] Build OCFL object/layout fixture and validate required inventory/version links.
5. [x] Run available reference validators; record unavailable tools without substituting claims.
6. Test extraction, checksum closure, provenance linkage, and deterministic reruns.
7. Compare results and publish an adoption recommendation with explicit limits.
8. Update the track and GitHub issue hierarchy only from receipts.
