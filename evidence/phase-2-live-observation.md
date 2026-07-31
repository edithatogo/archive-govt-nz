# Phase 2 live CKAN and Treasury observation

Status: observed locally

- Catalogue: `https://catalogue.data.govt.nz`
- Action API: v3
- CKAN: 2.10.9
- Capability observed: 2026-07-31T05:22:09.632168Z
- Treasury scope observed through: 2026-07-31T05:22:16.284413Z
- Treasury organisation: The Treasury (`the-treasury`,
  `4d08a178-e03b-4e97-b79d-83d9a7a35744`)
- Unique datasets reconciled: 54
- Live page counts: 54, 54, 54
- Page size and pages: 25 across 3 pages
- Scope SHA-256:
  `bb72d7fbad84b04aca6f39b39c76cf8e1d835887d86ac88a51b663a475f8414c`

The bounded client made one capability request, one organisation request, and
three sorted package-search requests. Every request succeeded on its first
attempt. Exact raw responses remain under the ignored local
`build/live/treasury-20260731T152100+1000-p25` directory; their paths, sizes,
and SHA-256 values are in the paired JSON receipt.

This establishes a read-only metadata observation at the stated times. It does
not establish resource-file capture, rights eligibility, derivative generation,
Hugging Face upload, Zenodo deposition, hosted scheduled verification, or
publication.
