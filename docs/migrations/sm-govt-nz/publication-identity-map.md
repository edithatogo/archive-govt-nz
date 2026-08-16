# Publication Identity Continuity Map

## 1. Core Publication Safety Principles

External publication identities (Hugging Face datasets, Zenodo DOIs, OSF projects) are persistent, citable scholarly and research assets. Consolidation of repository code **must never orphan, duplicate, or break existing publication URIs**.

1. **Retain Hugging Face Slugs**: The repository `edithatogo/corpus-social-media-government-nz` will continue receiving social-media archive snapshots, produced by `archive-govt-nz` CI.
2. **Preserve Zenodo Concept DOIs**: The Zenodo concept record `20991132` (`10.5281/zenodo.20991132`) will receive subsequent version depositions, preserving existing citations while updating producer provenance.
3. **Dual Dry-Run Verification**: No production publication cutover occurs until Track 12 passes comparative dual dry-run validation.

---

## 2. Publication Identity Registry

| Platform | Current Producer | Publication Identity / Slug | Future Producer | Continuity Strategy | Migration Gate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Hugging Face** | `edithatogo/sm-govt-nz` | [`edithatogo/corpus-social-media-government-nz`](https://huggingface.co/datasets/edithatogo/corpus-social-media-government-nz) | `edithatogo/archive-govt-nz` | Preserve slug; update Git provenance in `README.md` dataset card. | Track 12 |
| **Hugging Face** | `edithatogo/archive-govt-nz` | [`edithatogo/archive-govt-nz-global`](https://huggingface.co/datasets/edithatogo/archive-govt-nz-global) | `edithatogo/archive-govt-nz` | Canonical global catalogue repository. | Active |
| **Zenodo** | `edithatogo/sm-govt-nz` | Concept DOI: [`10.5281/zenodo.20991132`](https://doi.org/10.5281/zenodo.20991132) | `edithatogo/archive-govt-nz` | Preserve Concept DOI; publish new version depositions from target CI. | Track 12 |
| **Zenodo** | `edithatogo/archive-govt-nz` | Concept DOI: [`10.5281/zenodo.16872591`](https://doi.org/10.5281/zenodo.16872591) | `edithatogo/archive-govt-nz` | Canonical open data repository. | Active |
| **OSF** | `edithatogo/sm-govt-nz` | OSF Storage Target | `edithatogo/archive-govt-nz` | Unified RIOPA storage connector mirror. | Track 12 |

---

## 3. Metadata & Provenance Update Protocol

When `archive-govt-nz` performs the first production publication to `edithatogo/corpus-social-media-government-nz`:
- The dataset card YAML header will include:
  ```yaml
  language:
    - mi
    - en
  license: cc-by-4.0
  tags:
    - new-zealand
    - government
    - social-media
    - preservation
    - warc
  extra_gitaly:
    canonical_repository: "https://github.com/edithatogo/archive-govt-nz"
    consolidated_from: "https://github.com/edithatogo/sm-govt-nz"
    consolidation_revision: "24df5f2dea7cfcd85fecaa1a18845339f987eeec"
  ```
- The dataset description will explicitly document the migration timeline and provenance lineage.
