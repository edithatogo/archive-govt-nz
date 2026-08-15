# Track 19: Global Harvest Orchestration, Derivatives, and CI/CD Quality Frontiers

## Overview
Track 19 consolidates the mass preservation lifecycle for the New Zealand open government catalogue into an end-to-end orchestrated pipeline with automated Wayback triangulation, analytical columnar derivatives (Parquet & DuckDB), catalogue drift detection, and bleeding-edge CI/CD and mutation testing gates.

## Scope
- **Unified Harvester Orchestrator**: Single command (`tools/harvest_ckan.py`) managing discovery -> rights evaluation -> concurrent stream -> preservation packaging.
- **Wayback Triangulation & Broken URL Ingestion**: Recover missing/404 resources using Internet Archive and National Library CDX APIs without human intervention.
- **Columnar Analytical Derivatives**: Convert tabular captures to compressed Parquet and DuckDB databases with provenance tracing.
- **Incremental Catalogue Drift Engine**: Automated delta detection across crawls (`tools/detect_catalogue_drift.py`).
- **Bleeding-Edge Quality Gates**: Mutation testing for global policy, automated hygiene/slops gates, performance benchmark assertions, and scheduled CI/CD drift workflows.
