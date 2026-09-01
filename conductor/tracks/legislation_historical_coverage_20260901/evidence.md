# Evidence

Evidence is generated from exact donor batch bytes, target state receipts and independently refreshed public metadata. Historical invalidated parity receipts remain provenance only.

- Candidate partition: 68 exact batches, 33,693 unique IDs, concatenated SHA-256 `6f70fa9b596be2baa77bd885df1857e9b89c04013361c9ad80af722b0cc8493b`.
- Governed reviewed subset: 500 IDs bound to registry and seed bytes.
- Canonical target state: 552 works, records and CAS objects, bound to matching merge receipt and independent readback.
- Candidate IDs outside the governed subset: 33,193. This set boundary does not establish attempt or acquisition disposition; attempt, retrieval, expression, manifestation, normalisation and aggregate publication counts remain unknown rather than zero.
- Surface-specific public observations retain 6,609 rows for the historical Hub surface and 6 rows for the Zenodo snapshot without summing unlike surfaces.
- Generated report SHA-256: `b5c3731a800572a367cf6106d038b8ee9d3c03353c96f309866f2bc48fb99f11`.
- Generated correction-input SHA-256: `009fecd4a70e61e0b7b58646877d47b8560be8e4a91b24087de27c5c8e9541e1` (46 external claim-bearing inputs; generated outputs and this track are excluded; no inferred replacement acquisition count).
- Bound claim-correction manifest SHA-256: `d742ad3a6a7113affc8589773ecf92f9d9b961ceec4e746cfa4e17d2ad8c9800` (72 exact source lines and all 73 matching occurrences verified against current source and analyzer-input hashes).
- The package inventory binds all 552 CAS object paths to their SHA-256 identities among 560 package files.
- Focused qualification: 42 tests passed; 6/6 declared integrity mutants killed; Ruff passed. Two consecutive report generations were byte-identical.
- Full local validation reached 4,420 passes and 97.48% coverage; three unrelated cold-start Hypothesis deadline checks then passed unchanged in isolation.
- Hosted validation exposed and repaired a Windows text-mode fixture defect. A subsequent exact-head run passed Ubuntu and macOS but recorded 10.04 MB/s against the flaky 15 MB/s Windows CAS floor. Independent PR #339 recalibrated the Windows floor to 8 MB/s and passed the complete Ubuntu, macOS and Windows assurance matrix plus CodeQL, dependency review, workflow lint and patch coverage.
- PR #338 exact-head validation after integrating the merged CI repair remains pending; no delivery-complete claim is made before it passes and merges.
