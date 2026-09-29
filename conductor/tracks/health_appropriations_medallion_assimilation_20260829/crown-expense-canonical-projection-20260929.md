# BEFU 2026 Crown expense canonical projection

This is a source-faithful bridge from the retained BEFU-2026 Core Crown expense
Silver package into the existing `fiscal_context_fact` structural recordset. It
does not qualify a Crown denominator or produce a share measure.

## Exact inputs and rebuild

- Bronze object: `313ee040abd9a332cc36245da5a0c2cb0d38fe2cedc013d731c1f12db463b0d1`.
- Official locator: `https://budget.govt.nz/budget/excel/befu2026/befu26-data-expense-tables.xlsx`.
- Source vintage and observation: `BEFU-2026`, `2026-08-29T09:00:17Z`.
- Source-specific extraction: `befu-core-2026/v1`, transformation
  `treasury-befu-core-crown-expense-cache-2026/v1`.
- Retained Silver manifest SHA-256:
  `23ddc3fb0a3d4d6dc55a4731694f7d9e26f5ace1324d4a76456f1ad761abe651`.
- Projection verifies that manifest and every Parquet hash, reads the exact
  Bronze CAS object, reruns the pinned extraction, and compares all three
  regenerated source tables with the retained package before projecting.

## Canonical records

The projection yields 10 `fiscal_context_fact` rows for source year labels
2021–2030 and 80 direct lineage records. The five source-labelled Actual rows
and five Forecast rows remain distinct. Period tokens are encoded as
`year_label:YYYY`; valid-time dates remain null because the source financial-year
boundaries are not qualified. Amounts preserve each stored numeric cache token
and exact Decimal value. The canonical unit retains the source label
`($millions)`; ISO currency remains unknown. The canonical recordset does not
change or replace the source-specific Silver package.

Every output row retains the exact source object, locator, vintage, observation
identifier, and source record identifier. Rights remain `not_evaluated`.
Formula expressions are not evaluated; cache freshness and accounting basis
remain unverified. The projection does not select an expenditure denominator,
compare forecast outcomes, calculate a Crown share, or publish data.

## Assurance boundary

Focused tests exercise projection identity, exact values, null/unknown semantics,
lineage closure, immutable inputs, and rejection of changed products or manifest
pins. Integrated recovery rebuilds the source-specific Silver package and
canonical projection twice from Bronze and requires identical file/fact/lineage
hashes. This closes only the BEFU-2026 Core Crown context projection slice;
HYEFU and historical/Total Crown canonical projections, period/accounting
qualification, rights assessment, cross-source alignment, and full Gold/
Platinum acceptance remain open.
