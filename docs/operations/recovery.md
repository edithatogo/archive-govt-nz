# Disaster Recovery and Business Continuity Guide

`archive-govt-nz` provides reproducible, zero-network recovery guarantees backed by immutable Content-Addressed Storage (CAS) and W3C PROV-O lineage ledgers.

---

## 1. Recovery Objectives

- **Recovery Point Objective (RPO)**: < 6 hours (interval between scheduled ingestion snapshots).
- **Recovery Time Objective (RTO)**: < 15 minutes (full database and search index reconstruction from CAS).

---

## 2. Automated Recovery Drill

The repository includes an automated recovery harness in [`RestoreRehearsalHarness`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/recovery_harness.py).

### Running Disaster Recovery Rehearsal
```bash
# Execute local restore drill
uv run python -c "
from archive_govt_nz.recovery_harness import RestoreRehearsalHarness
harness = RestoreRehearsalHarness()
receipt = harness.execute_rehearsal()
print(f'Recovery status: {receipt.status}, objects recovered: {receipt.recovered_object_count}')
"
```

---

## 3. Cold Storage Reconstruction Steps

1. **Clone Canonical Repository**:
   ```bash
   git clone https://github.com/edithatogo/archive-govt-nz.git
   cd archive-govt-nz
   uv sync
   ```
2. **Download Remote Fixity Manifests**:
   ```bash
   archive-govt-nz archive --action verify
   ```
3. **Replay & Verify Bitstream Parity**:
   ```bash
   archive-govt-nz replay --verify-all
   ```
4. **Rebuild Analytical & Semantic Derivatives**:
   ```bash
   archive-govt-nz derivatives
   ```
