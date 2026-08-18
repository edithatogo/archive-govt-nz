# Migration Baseline: `corpus-legislation-nz` → `archive-govt-nz`

**Baseline Date**: 18 August 2026

---

## 1. Frozen Repository State

| Property | Donor (`corpus-legislation-nz`) | Canonical Target (`archive-govt-nz`) |
|---|---|---|
| **Repository** | `https://github.com/edithatogo/corpus-legislation-nz` | `https://github.com/edithatogo/archive-govt-nz` |
| **Baseline Commit SHA** | `749918c251da59dc890c19dfda2ab9a021fd8ca6` | `49e3b4cb234a1c468d1bcd191de67cea3a3c02c0` |
| **License** | MIT License | Apache-2.0 |
| **Total Conductor Tracks** | 48 donor tracks | 15 completed consolidation tracks |
| **Total Issues** | 65 (21 open, 44 closed) | 0 open |
| **Workflows** | 25 workflows | 15 workflows (CI, discovery, harvest) |
| **Seed Inventory** | 33,693 search-derived works | Canonical multi-source registries |
| **Historical Batches** | 68 period-sharded batches | Content-Addressed Storage (CAS) |

---

## 2. Non-Donor Boundary Isolation

The repository **`edithatogo/legislation`** is explicitly excluded from consolidation:
- Retains ownership of `nz-legislation-tool` (npm package).
- Retains ownership of `nzlegislation` interactive CLI.
- Retains standalone MCP server and registry identities.
- Acts as a downstream consumer of canonical datasets exported by `archive-govt-nz`.
