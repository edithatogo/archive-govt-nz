# Track 7 Specification: Publication and Archive-Distribution Alignment

## Purpose
Unify multi-target publication semantics across Hugging Face, Zenodo, OSF, and GitHub Releases while guaranteeing external publication identity preservation.

## Context & Objectives
1. Implement universal `ArchivePacket` and `PublicationReceipt` models.
2. Maintain Hugging Face living dataset sync to `edithatogo/corpus-social-media-government-nz` and `edithatogo/archive-govt-nz-global`.
3. Retain Zenodo Concept DOIs (`10.5281/zenodo.20991132` and `10.5281/zenodo.16872591`), generating verified dual-signed version depositions with RO-Crate and BagIt manifests.
4. Establish OSF mirror adapter under RIOPA storage protocol.
5. Materialize columnar Parquet and DCAT-AP knowledge graphs alongside raw archives.

## Deliverables
- `src/archive_govt_nz/publication/core.py`
- `src/archive_govt_nz/publication/huggingface.py`
- `src/archive_govt_nz/publication/zenodo.py`
- `src/archive_govt_nz/publication/osf.py`
- Publication verification test suite
