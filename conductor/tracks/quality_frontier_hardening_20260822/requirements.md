# Requirements: Quality Frontier Hardening (MoSCoW)

## Must

- **M-01**: A bounded mutation suite (`tools/mutation_gazette.py`) targets the
  gazette domain validation module (policy-critical integrity logic) with a
  100% kill rate enforced.
- **M-02**: The mutation suite is registered as a first-class stage in the
  repository assurance harness (`STAGES` in `src/archive_govt_nz/assurance.py`)
  so every future `tools/check.py` run enforces it.
- **M-03**: Mutations must cover chronology enforcement, fixity-hash field
  binding, URI scheme acceptance, year bounds and boolean-type rejection, and
  required-identity checks.
- **M-04**: The suite follows the established mutation-tool contract
  (`archive-govt-nz.mutation/v1` receipt, unique-target enforcement, isolated
  source tree per mutant).

## Should

- **S-01**: Boolean-year rejection test added before mutation enforcement (TDD).

## Could

- **C-01**: Additional mutation suites for other new domains in future tracks.

## Won't (this track)

- No new CI workflows or external-service integrations.
- No changes to existing mutation suites or their sources.