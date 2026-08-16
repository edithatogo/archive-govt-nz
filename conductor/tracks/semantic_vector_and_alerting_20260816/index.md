# Track 20: Semantic Knowledge Graph, Hybrid Vector Search, and Automated Webhook Dispatch

## Overview
Track 20 elevates the preservation estate into an intelligent queryable knowledge graph with hybrid BM25 + cosine vector search over catalogue metadata, DCAT-AP/RO-Crate semantic linking, and automated rich webhook notifications for CI/CD preservation runs.

## Scope
- **Semantic Knowledge Graph**: Map CKAN metadata and RO-Crate packages into standardized DCAT-AP semantic graphs with organization, theme, and temporal entity links.
- **Hybrid Vector & Lexical Search**: Implement fast BM25 + cosine vector embedding search across government dataset titles, descriptions, and schemas using DuckDB/numpy.
- **Automated Webhook Dispatcher**: Rich alerting system supporting Discord, Slack, and generic webhooks to broadcast harvest metrics and Hugging Face snapshot links.
- **Search CLI & Graph Exporter**: Tooling (`tools/query_knowledge_graph.py` and `tools/notify_webhook.py`) to query and notify.
- **Quality Gates & Snapshots**: Strict BasedPyright typing, Syrupy snapshot assertions, property fuzzing, and complete branch coverage.
