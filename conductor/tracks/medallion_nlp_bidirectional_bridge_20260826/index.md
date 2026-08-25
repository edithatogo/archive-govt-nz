# Track: Medallion NLP Bi-Directional Bridge, Bleeding-Edge OCR & Ontological Synthesis

- **ID:** `medallion_nlp_bidirectional_bridge_20260826`
- **Type:** feature
- **Status:** `new` (2026-08-26)
- **Repositories:** [`edithatogo/archive-govt-nz`](https://github.com/edithatogo/archive-govt-nz), [`edithatogo/nlp-policy-nz`](https://github.com/edithatogo/nlp-policy-nz)

## Overview

Establishes a hardened, high-performance bi-directional bridge between the Medallion Data Engine in `archive-govt-nz` and the NLP/Policy Extraction Suite in `nlp-policy-nz`.

Key capabilities:
1. **International Ontologies:** Akoma Ntoso 3.0, ELI, WHO ATC/SNOMED, and FIBO/NZBN integrated into Medallion schemas.
2. **Layout-Aware OCR & Multi-Pattern Matcher:** Dual-column reading order reconstruction, de-hyphenation, and sub-millisecond Aho-Corasick statutory matching.
3. **Resilient Streaming & Checkpointing:** Polars streaming chunk transformation with `.checkpoint` offset recovery.
4. **Ingestion CLI & spaCy Components:** `nlp-policy-nz ingest` CLI and `@Language.component` decorators for Gazette, Hansard, and Medico-Legal extraction.
5. **Reverse Gold Knowledge Graph Ingestion:** Extracts feed back into DuckDB `v_gold_extracted_entities` and LanceDB vector indexes.
6. **Dynamic FastMCP Server:** Automatically generates FastMCP tools from the unified 7-domain Medallion schema registry.

## Documents
- [Specification](./spec.md)
- [Implementation Plan](./plan.md)
- [Metadata](./metadata.json)
