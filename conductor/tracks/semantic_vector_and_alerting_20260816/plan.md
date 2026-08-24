# Implementation Plan — Track 20: Semantic Knowledge Graph, Hybrid Vector Search, and Automated Webhook Dispatch

## Phase 1 — Semantic Knowledge Graph & DCAT-AP Mapping
- [x] Task: Implement src/archive_govt_nz/knowledge_graph.py mapping metadata into DCAT-AP/RO-Crate graphs.
- [x] Task: Write tests for knowledge graph generation in tests/tools/test_track20_tools.py.
- [x] Task: Phase Verification & Checkpoint.

## Phase 2 — Hybrid Vector & Lexical Search Engine
- [x] Task: Implement src/archive_govt_nz/search.py supporting BM25 and cosine vector search.
- [x] Task: Write search tests in tests/tools/test_track20_tools.py.
- [x] Task: Phase Verification & Checkpoint.

## Phase 3 — Automated Webhook Notification Engine
- [x] Task: Implement src/archive_govt_nz/webhook_notifier.py and tools/notify_webhook.py.
- [x] Task: Write webhook tests in tests/tools/test_track20_tools.py.
- [x] Task: Phase Verification & Checkpoint.

## Phase 4 — CLI Tooling and Quality Verification
- [x] Task: Implement tools/query_knowledge_graph.py.
- [x] Task: Integrate into locked validation harness and verify test coverage.
- [x] Task: Full verification with tools/check.py, PR, and merge.
