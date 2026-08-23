# Evidence: Quality Frontier Hardening

## Mutation Receipt
- Tool: `tools/mutation_gazette.py`
- Source under mutation: `src/archive_govt_nz/domains/gazette/validate.py`
- Result: **7/7 killed, status: passed** (receipt `build/mutation-gazette.json`)
- Mutants: notice_id_field, hash_wrong_field, uri_scheme_drop_https,
  chronology_direction, iso_parse_guard, year_bounds_flip, bool_year_accepted
- Detecting suite: `tests/domains/test_gazette_service.py` (16 tests)

## Gate Registration
- Stage `mutation-gazette` appended to `STAGES` in
  `src/archive_govt_nz/assurance.py` after `mutation-adapters`.
- Per-file ignores added: `"tools/mutation_gazette.py" = ["S603", "S607"]`.