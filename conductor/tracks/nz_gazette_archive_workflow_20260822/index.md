# Track: NZ Gazette Archive Workflow

- **ID**: `nz_gazette_archive_workflow_20260822`
- **Type**: feature
- **Status**: `completed` (2026-08-22)
- **Created**: 2026-08-22

## Overview

Implements the production gazette archive workflow: a domain service layer over the
existing `NZGazetteAdapter`, a deterministic weekly harvest orchestrator with
checkpoint state, a scheduled CI workflow, and evidence receipts. Addresses donor
issues #142–#144 (Gazette freshness, workflow, cross-source comparison) within the
official/DigitalNZ scope; historical gazette sources remain deferred.

## Documents
- [Requirements (MoSCoW)](./requirements.md)
- [Execution Plan](./plan.md)
- [Evidence](./evidence.md)
- [Run Log](./runlog.md)