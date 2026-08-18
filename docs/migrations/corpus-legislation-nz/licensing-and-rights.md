# Licensing & Rights Classification: Legislation & Gazette Corpus

**Document Version**: `1.0.0`  
**Date**: `2026-08-18`

---

## 1. Classification Framework

Rather than applying a single universal `crown_copyright_open` assumption across all records, the target preservation repository enforces granular source- and artifact-specific rights classifications:

| Artifact Category | Legal Basis | Applicable License | Permitted Distribution |
|---|---|---|---|
| **Legislation Statutory Text** (XML/HTML from PCO) | Section 27, Copyright Act 1994 (No copyright in NZ legislation) / Crown Copyright under NZGOAL | Open (CC-BY 4.0 / Public Domain) | Full bulk distribution in Parquet / JSONL / CAS |
| **Website Presentation & Shell** (`legislation.govt.nz`) | Crown Copyright / PCO terms of use | Informational | Preserved in CAS; downstream redistribution filtered to clean text |
| **Official NZ Gazette Notices** | Crown Copyright / Department of Internal Affairs | Open (CC-BY 4.0 / NZGOAL) | Full text publication with provenance binding |
| **Historical Gazette Documents** (Pre-2014) | Archives NZ / National Library / Public Domain | Public Domain / CC-BY | Direct CAS archive with rights metadata |
| **Incorporated-by-Reference & Standards** | Third-party copyright (e.g. ISO/NZS standards referenced in regs) | Proprietary / Restricted | Metadata, hashes, and acquisition URI preserved only; payload restricted from public bundle |
| **Repository Software & Tooling** | `corpus-legislation-nz` (MIT) & `archive-govt-nz` (Apache-2.0) | Multi-licensed / Open Source | Source code distribution under Apache-2.0 with MIT attribution |

---

## 2. Fair Dealing & Provenance Rules
- If an instrument includes third-party attachments or schedules where the license is uncertain, the target repository stores the raw bitstream in content-addressed storage for preservation fixity, but marks `distribution_eligible: false` in the public release manifest.
