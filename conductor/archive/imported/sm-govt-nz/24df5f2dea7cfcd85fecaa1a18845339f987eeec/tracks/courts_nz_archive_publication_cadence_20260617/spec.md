# Specification - Courts of New Zealand Archive Publication Cadence

Clarify and implement the publication cadence for the Courts of New Zealand
archive corpus. Archive capture is already scheduled; external publication needs
an explicit cadence so "continuous Hugging Face" and "episodic Zenodo" have
machine-checkable meanings.

## Requirements

1. Archive capture must remain independent of outbound syndication.
2. Hugging Face should receive regular dataset updates when secrets are valid and
   publication is enabled.
3. Zenodo should remain a deliberate citable snapshot lane, not an uncontrolled
   every-run deposit.
4. Manual publish runs must continue to support `publish=true` with a clear
   artifact-only default.
5. Publication status should be visible from committed reports.

## Done

- Scheduled Hugging Face publication behavior is documented and implemented.
- Zenodo snapshot cadence and approval gate are documented.
- Latest publication report records whether the run was artifact-only, Hugging
  Face-published, Zenodo-drafted, or Zenodo-published.
- Dataset freshness is checked in CI or a scheduled monitor.
- The multi-source archive track points to this cadence track for remaining
  publication operations.
