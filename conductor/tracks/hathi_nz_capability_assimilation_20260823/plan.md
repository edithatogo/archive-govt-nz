# Implementation Plan: HathiTrust NZ Historic Corpus Capability Assimilation

## Phases & Tasks

### Phase 1: Capability Inspection & Inventory
- [ ] Task: Inventory reusable modules, fixtures, and schemas from `edithatogo/hathi-nz`.
- [ ] Task: Define domain contract and schema specifications in `schemas/`.
- [ ] Task: Conductor - User Manual Verification 'Capability Inspection' (Protocol in workflow.md).

### Phase 2: Domain Engine & Normalizer Implementation
- [ ] Task: Port and refactor domain normalizer using Polars and PyArrow.
- [ ] Task: Connect domain engine to Content-Addressed Storage (CAS) and Silver Parquet exporter.
- [ ] Task: Write characterization and unit test suites with >=95% branch coverage.
- [ ] Task: Conductor - User Manual Verification 'Domain Engine Implementation' (Protocol in workflow.md).

### Phase 3: Integration, Parity & Verification
- [ ] Task: Implement parity validation harness and negative-control test suite.
- [ ] Task: Wire domain queries into CLI and FastMCP server.
- [ ] Task: Run full 19-stage validation harness (`tools/check.py`) and record evidence receipt.
- [ ] Task: Conductor - User Manual Verification 'Integration & Parity' (Protocol in workflow.md).
