# Specification — Track 18: Global CKAN Catalog Harvester

## Overview

This track establishes a high-throughput, catalogue-wide preservation pipeline for `data.govt.nz` that replaces agency-by-agency scraping with a unified four-stage engine: Global Discovery, Rights & Policy Filtering, Bounded Concurrent Capture, and Broken URL / Tombstone Reconciliation.

## Architecture & Workflows

1. **Global Discovery (`tools/discover_global_ckan.py`)**:
   - Paginates through CKAN `package_search` (`q="*:*"`, `rows=1000`, `sort="id asc"`).
   - Emits raw page observations and a canonical catalogue manifest containing all datasets (~5,000+) and resources (~20,000+).

2. **Automated Rights & Resource Policy Gate**:
   - Evaluates dataset and resource metadata against known open-data license strings.
   - Partitions resources into `eligible` (admitted for download) vs `rights_restricted` / `unknown_license` (recorded as tombstones).

3. **High-Throughput Bounded Ingestion**:
   - Streams eligible resources to temporary storage, verifying checksums (SHA-256 / BLAKE3) and promoting into CAS `objects/`.
   - Respects per-domain concurrency limits and total byte/time budgets.

4. **Broken Link & Exception Reconciliation**:
   - Compiles all HTTP errors (404, 410, 500, timeouts) into a machine-readable ledger.
   - Prepares follow-up actions (Wayback Machine triangulation, CKAN DataStore fallback).
