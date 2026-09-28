# QES source-native Silver v3 recovery

The source-native QES adapter changed in PR #525 to retain three additional
lineage rows per quarter. The previously retained v2 Silver package
(`35114105c86085ee49aeb97ac9f8d8b696ef72692b5eea12d348496a8b920d41`) therefore
does not reproduce the current adapter contract: it contains 180 field-lineage
rows, while the nine-quarter current build contains 207. The v2 directory and
all source bytes remain untouched.

The QES Bronze workbook is pinned by the context census to SHA-256
`1af2e7e37f1c108a2656842cf1f519c903e1a982bcdc03ee02d0ad888ebc3a97`, locator
and observation timestamp. A separate v3 package was rebuilt from those exact
Bronze bytes at the external path
`/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/silver/raw-qes-2026q2-20260831-v3`.
Its manifest SHA-256 is
`0bf89bd6c10a0458ef4c578b209c3252292961976d2f50b3c27fe92907c3cb04`; it records
9 normalized facts, 207 field-lineage rows, and 6,021 inventoried cells.
Independent clean-room recovery runs rebuilt v3 twice with identical files.

Context Gold now pins v3. This is an adapter/recovery reproducibility repair;
it does not qualify QES currency, sex/adjustment semantics, annual aggregation,
rights, deflator status, or analytical eligibility. It does not replace v2 or
alter the published candidate.
