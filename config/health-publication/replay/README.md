# Historical transport witnesses

These Budget 2025 Vote Health extraction files preserve the raw-manifest hash
used in published canonical record identities. Source workbook SHA-256 and
observation metadata are in the manifest. Attribution is The Treasury,
New Zealand, Crown Copyright, licensed CC BY 4.0. The exact publisher page and
workbook are qualified in `../static/metadata/budget_recovery_licence_and_lineage.json`.

The workflow independently rebuilds the original workbook. It requires exact
manifest equality except transport output hashes, plus exact Arrow schemas,
metadata and values for every raw table, before reusing these historical bytes.
No rows or identity mismatches are normalized away.
