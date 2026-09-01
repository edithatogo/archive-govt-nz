# Evidence

Evidence is generated from exact donor batch bytes, target state receipts and independently refreshed public metadata. Historical invalidated parity receipts remain provenance only.

- Candidate partition: 68 exact batches, 33,693 unique IDs, concatenated SHA-256 `6f70fa9b596be2baa77bd885df1857e9b89c04013361c9ad80af722b0cc8493b`.
- Governed reviewed subset: 500 IDs bound to registry and seed bytes.
- Canonical target state: 552 works, records and CAS objects, bound to matching merge receipt and independent readback.
- Unknown disposition: 33,193 candidate IDs; attempt, retrieval, expression, manifestation, normalisation and aggregate publication counts remain unknown rather than zero.
- Surface-specific public observations retain 6,609 rows for the historical Hub surface and 6 rows for the Zenodo snapshot without summing unlike surfaces.
- Generated report SHA-256: `b5c3731a800572a367cf6106d038b8ee9d3c03353c96f309866f2bc48fb99f11`.
- Generated correction-input SHA-256: `b59b97c39b198ecab7d6e6f372dd6ec8101c461be628fc7808b4b33d2d667e4c` (46 external claim-bearing inputs; generated outputs and this track are excluded; no inferred replacement acquisition count).
- Focused qualification: 35 tests passed; historical-coverage suite 17 tests passed; 6/6 declared integrity mutants killed; Ruff passed. Two consecutive report generations were byte-identical.
