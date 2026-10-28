# Historical Gold and donor reconciliation

The read-only historical Gold control binds the raw Gold and retained historical
comparison manifests and their Parquet outputs to exact SHA-256 pins. It checks
that the donor identity and counts agree with the pinned disposition receipt,
then accounts for every Health Gold fact by source record, year, source hash,
label, exact Decimal and coordinate. Differences require matching accepted
retain-both dispositions, source/donor value hashes, null replacement and no
publication approval. The command emits deterministic JSON and never writes to
or changes input packages.

The retained Fiscal 2024 evidence produced 53 reconciled Gold records: 23 exact
matches, 29 source-only rows and one value difference. Two independent calls
produced identical canonical JSON, SHA-256
`e5fd5b131e36c3bed7f03f09178cf8b4ed6b328a9f089e392fe38edab002051a`.
The Gold manifest pin is `ec68a03f597c7792da4337f2babfcb6615c2e6162a3125042c2b8ef6b7665835`;
the comparison manifest pin is `4847b9b50a08a1f8d2b42627fd496bb0dafe5a661b0d934db41db2d1dbca234e`;
the disposition receipt pin is `547d901ec8c4b2a467351d1a69ba6391d728b699ff05013688c3fa4de6a73ea0`.

This control uses an existing source/donor comparison rather than reparsing the
workbook or database. It does not assert source completeness, cross-source
comparability, rights or publication approval. Other Gold and recovery gates
remain open. Focused reconciliation and pin/tamper tests passed; full harness
and hosted delivery are separate.
