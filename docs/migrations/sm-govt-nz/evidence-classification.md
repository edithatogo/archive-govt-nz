# Evidence Classification: Consolidation Programme

This document defines the 10 formal evidence classes utilized to distinguish in-memory tests, static fixtures, synthetic property fuzzing, and simulations from live network and production publication evidence.

---

## Defined Evidence Classes

| Class | Definition | Confidence Level |
|---|---|---|
| **unit** | Isolated in-memory component tests with mock boundaries. | Verification |
| **fixture** | Static deterministic data fixtures mimicking real-world payloads. | Verification |
| **deterministic_simulation** | Reproducible multi-cycle shadow runs and state-machine drills. | Validation |
| **synthetic** | Property-based fuzzing and edge exploration (Hypothesis). | Verification |
| **replay** | Zero-network deterministic replay of historical captured payloads. | Validation |
| **local_integration** | End-to-end multi-module execution against local CAS and SQLite stores. | Validation |
| **remote_integration** | Interaction with external API endpoints or staging environments. | High |
| **live_canary** | Live shadow capture against real public government endpoints. | High |
| **production** | Production pipeline execution producing immutable release artifacts. | Authoritative |
| **external_readback** | Post-publication bitstream and hash readback from remote registries. | Authoritative |

---

## Consolidation Track Evidence Map

| Track | Track Title | Primary Class | Supporting Classes | Status Qualification |
|---|---|---|---|---|
| **Track 1** | Consolidation Baseline & Authority | `fixture` | `unit`, `local_integration` | Baseline schemas and evidence inventory verified. |
| **Track 2** | Conductor Lineage Reconciliation | `production` | `local_integration` | 39 donor tracks immutably archived. |
| **Track 3** | Capability & Interface Reconciliation | `local_integration` | `unit` | 22-row capability matrix reconciled. |
| **Track 4** | Canonical Archive Contracts | `production` | `unit`, `fixture`, `local_integration` | Schemas and 350+ agency seed registry active. |
| **Track 5** | Source Adapter Migration Programme | `local_integration` | `unit`, `fixture`, `replay` | Multi-source async adapters implemented. |
| **Track 6** | Preservation, Replay & Recovery Assimilation | `replay` | `unit`, `fixture`, `local_integration` | WARC/WACZ packaging & recovery harness verified. |
| **Track 7** | Publication & Distribution Alignment | `local_integration` | `unit`, `fixture` | Croissant, RO-Crate & DCAT-AP metadata verified. |
| **Track 8** | CLI/MCP Interface Convergence | `local_integration` | `unit` | 9 CLI subcommands & backward-compatible aliases active. |
| **Track 9** | Differential/Parity Harness | `synthetic` | `unit`, `fixture`, `replay` | Differential parity models & Hypothesis fuzzing verified. |
| **Track 10** | Canary Migration & Dual Operation | `deterministic_simulation` | `unit`, `fixture` | 2-cycle dual shadow run & rollback verified. |
| **Track 11** | Capability Assimilation & Architectural Refactor | `production` | `unit`, `synthetic`, `local_integration` | Stdlib JSON logging, unified HTTP & adapter mutation gate. |
| **Track 12** | Release Cutover & Publication Continuity | `deterministic_simulation` | `unit`, `fixture` | Release cutover packaging & root fixity calculation verified. |
| **Track 13** | Observation, Donor Deprecation & Archival | `production` | `external_readback` | Donor repository archived (`isArchived: true`), 0 open issues/PRs. |
| **Track 14** | Post-Consolidation RIOPA Interoperability | `local_integration` | `unit`, `fixture` | RIOPA v1 export contracts & boundary isolation verified. |
