# FOI original-byte preservation

The receiver can prepare and cold-restore a bounded retained fyi-cli capture.
This is a local preservation operation, not public delivery or country completion.
Use a capture inventory SHA-256 taken from independent hosted evidence, not one
computed from an untrusted downloaded package immediately before validation.

The capture receipt is a JSON object with `source_id`, `country`, `captured_at`
(UTC), `source_revision` (full Git SHA), `source_run_id`, `adapter_version`, and
`inventory_sha256`. These identify the capture rather than the packaging time.

```sh
uv run --locked python tools/foi_package.py prepare \
  --root build/retained-capture --capture-receipt build/capture-receipt.json \
  --output build/foi-candidate
uv run --locked python tools/foi_package.py verify \
  --root build/foi-candidate --manifest-sha256 "$TRUSTED_MANIFEST_SHA256"
uv run --locked python tools/foi_package.py restore \
  --root build/foi-candidate --manifest-sha256 "$TRUSTED_MANIFEST_SHA256" \
  --output build/foi-restored
```

The package contains original files and stored WARC response bodies deduplicated
by SHA-256 in `raw.tar`. Four indexes (`objects`, `resources`, `requests`, `events`)
are supplied as JSONL and Parquet. Original JSON remains separate from derived
indexes. Restoration validates the entire package, reconstructs original paths
without archive extraction, then rebuilds the indexes and compares them.
An existing different candidate or restore destination is never overwritten.

Inputs are bounded to 10,000 inventory files, 2 GiB of retained files and 2 GiB
of expanded WARC data. Preserve larger captures as separate bounded shards.
Treat candidate folders as sensitive: do not commit them, serve active HTML, or
upload them without exact source-rights and privacy review. Files are created
under a private staging directory; local disk storage is not encrypted by this tool.

The package indexes describe retained responses. They do not establish that all
expected attachments, all source requests, or historical revisions were captured.
The pinned adapter silently skips attachment HTTP 404 responses; explicit gap
accounting is still required. A public Hugging Face repository or a successful
capture job does not resolve that limitation. NZ automatic dispatch remains paused
until the track's retention, eligibility and recovery requirements are met.

Focused integrity mutations can be run with
`uv run --locked python tools/mutation_foi_package.py`.
