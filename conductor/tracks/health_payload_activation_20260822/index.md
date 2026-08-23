# Track: Health Payload Activation

- **ID**: `health_payload_activation_20260822`
- **Type**: feature
- **Status**: `in_progress`
- **Created**: 2026-08-22

## Overview

Builds the deterministic eligibility-evaluation machinery for the zero-payload
health capture boundary left by Track 14 (`health_payload_capture_20260802`).
The evaluator re-classifies recorded decision-required resources against
machine-checkable licence-evidence criteria, stays fail-closed without
affirmative evidence, and emits a stable receipt so future licence enrichment
becomes a data update rather than a code change. No rights decisions are made;
no retrieval occurs in this track.

## Documents
- [Requirements (MoSCoW)](./requirements.md)
- [Execution Plan](./plan.md)
- [Evidence](./evidence.md)
- [Run Log](./runlog.md)