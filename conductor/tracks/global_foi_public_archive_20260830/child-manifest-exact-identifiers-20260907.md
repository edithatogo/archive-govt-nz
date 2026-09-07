# Child-manifest exact identifier follow-up — 2026-09-07

Local-only correction to c3630b7f. Independent review found that JSON Schema
patterns ending in dollar can accept a trailing newline. Schema validation alone
did not establish exact snapshot revisions; the original dated receipt is
preserved, not retroactively strengthened.

The canonical child boundary now explicitly fullmatches snapshot_revision and
manifest_sha256 after parsing current.json, before any manifest metadata lookup
or download. It also fullmatches manifest source_revision,
capture_inventory_sha256 and every file sha256, plus source_run_id and
adapter_version, before accepting the manifest.

Audit: source hf_revision and repository syntax already use fullmatch. Source
identity/country bind by exact equality to the pinned catalogue; manifest paths
bind to the closed expected set, and schema versions/tables use exact constants.
Generated receipt digests come from hashlib. The observed latest Hub head is not
used as an immutable reference. Root and packaged schemas are unchanged and their
byte parity remains tested; this is additive canonical-boundary validation, not
a legacy validator or default-v1 behavior change.

## Validation

Seven new unit negatives failed before the fix, then passed. The publisher
regression supplies a valid-length revision prefix followed by an escaped newline,
with correct pointer byte length. It permits only the pointer read and verifies
no manifest lookup/download, no catalogue writes and unchanged existing files.

Exact focused lane (no PYTHONPATH override, no full harness):

```sh
UV_OFFLINE=true uv run --locked pytest tests/test_foi_child_manifests.py tests/test_foi_child_manifest_mutants.py tests/test_foi_delivery.py tests/test_foi_package.py tests/test_publish_foi_cli.py -q --cov=archive_govt_nz.foi_child_manifests --cov=archive_govt_nz.foi_publication --cov-report=term-missing
```

187 passed in 15.00s on Python 3.14.6. Both measured modules retain 100% statement
and branch coverage. Eight static guard mutants were killed, including disabling
each of the five added revision/digest checks. Scoped locked-offline Ruff lint,
format check and BasedPyright passed on the production module and three test files.

Conductor implement/review applied to this scoped correction. No parent files,
historical evidence, schemas, source pins, schedules or lifecycle states changed.
All transport evidence is mocked: no external calls, publication, raw-object
verification or rights approval. Parent review/full gate remains separate.
