# Specification: Legislation Post-Cutover Production Steady-State Operations

## Architecture & Workflows
```text
Cron Trigger ('0 18 * * 0') / Manual Dispatch
         │
         ├──> [Automatic Prior State Discovery] (3-tier fallback)
         ├──> [NZ Legislation API Incremental Harvest]
         ├──> [Three-Strata B0/B1/B2 Ingestion]
         ├──> [Silver Parquet & Bitemporal Timeline Update]
         └──> [Artifact Upload: legislation-state-${{ run_id }}]
```

## Monthly Reconciliation Flow
```text
Cron Trigger ('0 6 1 * *') / Manual Dispatch
         │
         ├──> [Discover Latest Successful Harvest Artifact]
         ├──> [Run Offline Fixity & Inventory Check]
         └──> [Emit Reconciliation Receipt]
```
