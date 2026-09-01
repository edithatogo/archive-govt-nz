# corpus-legislation-nz — archived migration source

> [!IMPORTANT]
> This repository is archived and frozen. The canonical repository for ongoing
> New Zealand government archive preservation work is
> [`edithatogo/archive-govt-nz`](https://github.com/edithatogo/archive-govt-nz).

The final operational donor commit is
[`b40587f1b1aec7356a0f623916fcc8212397d283`](https://github.com/edithatogo/corpus-legislation-nz/commit/b40587f1b1aec7356a0f623916fcc8212397d283),
committed on 21 August 2026. The repository was subsequently archived. Its Git
history remains public as migration provenance; new runtime development belongs
in `archive-govt-nz`.

## Public dataset and citation identities

- Living Hugging Face dataset: [`edithatogo/corpus-legislation-nz`](https://huggingface.co/datasets/edithatogo/corpus-legislation-nz)
- Historical Hugging Face dataset: [`edithatogo/corpus-legislation-nz-historical`](https://huggingface.co/datasets/edithatogo/corpus-legislation-nz-historical)
- Zenodo concept DOI: [`10.5281/zenodo.20592539`](https://doi.org/10.5281/zenodo.20592539)
- 2026 Zenodo version DOI: [`10.5281/zenodo.20592540`](https://doi.org/10.5281/zenodo.20592540)
- Canonical source and preservation authority: [`edithatogo/archive-govt-nz`](https://github.com/edithatogo/archive-govt-nz)

For a fixed citation, use the relevant immutable Zenodo version DOI and its
record metadata. For current dataset access, cite the exact Hugging Face commit
revision in addition to the dataset identity. Migration and restoration
evidence is maintained in the canonical repository under
[`evidence/migrations/corpus-legislation-nz/`](https://github.com/edithatogo/archive-govt-nz/tree/main/evidence/migrations/corpus-legislation-nz).

The separate [`edithatogo/legislation`](https://github.com/edithatogo/legislation)
product is independent. It was not absorbed into this migration and this redirect
does not change its authority or release history.

## Licence and source-content boundary

Repository software retains its applicable open-source licence and attribution.
Legislation, website presentation, incorporated material, archives, and other
source content retain their own copyright, licence, access, provenance, and
reuse conditions. Archiving this Git history, linking public datasets, or moving
canonical development does **not** relicense all source content and does not by
itself prove complete legislative coverage.

## Restore

Use the canonical Prompt 19 bundle-verification receipt and its exact SHA-256
before restoring a preservation bundle. Verify with Git-native `git bundle
verify`, clone into a new isolated directory, run strict object-graph checks,
and compare the bundle's advertised refs with the receipt. Do not treat a draft
release, an expiring Actions artifact, or a successful clone alone as durable or
complete preservation evidence.
