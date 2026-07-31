---
dataset_info:
  config_name: default
  features:
    - name: dataset_id
      dtype: string
    - name: name
      dtype: string
    - name: title
      dtype: string
    - name: organization
      dtype: string
    - name: metadata_modified
      dtype: string
    - name: resource_count
      dtype: int64
  language:
    - en
  license: other
tags:
  - new-zealand
  - government
  - treasury
  - public-finance
  - ckan
  - modality:tabular
  - format:parquet
  - format:json
  - provenance
---

# Archive Govt NZ — Treasury normalized dataset

Viewer-facing normalized metadata derivative for the Treasury CKAN archive.
This repository contains no original payload objects. Original metadata,
source files, checksums, rights decisions, and transformation evidence remain
in [archive-govt-nz-treasury](https://huggingface.co/datasets/edithatogo/archive-govt-nz-treasury).

Transformation: `derivatives/v1`; 54 dataset rows; unknown CKAN fields are not
projected into this derivative. The derivative is not a substitute for the
source archive.
