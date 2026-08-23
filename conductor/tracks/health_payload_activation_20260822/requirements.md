# Requirements: Health Payload Activation (MoSCoW)

## Must

- **M-01**: A deterministic eligibility evaluator
  (`tools/evaluate_health_payload_eligibility.py`) re-classifies the 158
  recorded `decision-required` Ministry of Health resources against explicit,
  machine-checkable licence-evidence criteria.
- **M-02**: Fail-closed default — resources without affirmative recorded or
  supplied licence evidence remain `decision-required`; the evaluator must not
  invent eligibility.
- **M-03**: Accepts an optional `--licence-map` JSON input (dataset_id →
  licence_id) so future live CKAN licence enrichment feeds classification
  without code changes.
- **M-04**: Emits a schema-stable machine-readable receipt
  (`archive-govt-nz.health-eligibility/v1`) with per-resource dispositions,
  counts, and the exact criteria applied.
- **M-05**: Open-licence recognition covers CC0, CC-BY variants, OGL-NZ, and
  public-domain identifiers; everything else is non-eligible.
- **M-06**: Focused test suite covers: eligible path, restricted licence,
  unknown licence, missing map entry, malformed inputs, and receipt counts.

## Should

- **S-01**: Evaluation is pure/offline by default; no network access.

## Could

- **C-01**: Live CKAN licence enrichment as a future separate track.

## Won't (this track)

- No rights decisions, no payload downloads, no publication actions.
- No changes to the existing fail-closed capture engine.