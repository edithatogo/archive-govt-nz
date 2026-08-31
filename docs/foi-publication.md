# Verified FOI publication

The public source catalogue and raw source payloads have different eligibility
boundaries. The existing user instruction authorizes a public metadata catalogue
at `edithatogo/foi-source-catalogue`. It does not establish redistribution rights
or privacy clearance for each raw FOI source.

```sh
uv run --locked python tools/publish_foi.py catalogue \
  --create-catalogue-repository --receipt build/catalogue-publication.json
```

The optional creation flag only creates the named public catalogue. It never
converts an existing private repository. The command verifies the configured
operator account, pinned seed bytes and current child-repository visibility.
The catalogue retains baseline child revision pins and their observation dates;
visibility rechecking does not claim that those revisions contain complete raw
archives or are the latest capture revision.

The publisher stores files below `snapshots/<manifest-sha256>/`, downloads every
file anonymously into fresh storage, validates reconstruction, and only then
updates `current.json` and the dataset card. Both commits compare the expected
parent revision. Existing conflicting snapshot bytes are never overwritten.
An interrupted upload leaves the prior pointer unchanged. An identical retry
verifies existing bytes and the prior pointer's exact snapshot revision.
Dataset Viewer availability is a separate observation, not a preservation gate.
The card supplies separate table configurations for the indexes present.

Raw publication additionally requires `--package`, an independently trusted
`--manifest-sha256`, and an explicit `--decision` JSON document. The document must
bind that hash, `source_id`, and the registry's existing `repo_id`; name the
accountable reviewer `edithatogo`; set `rights_status` and `privacy_status` to
`approved`; specify `purpose` as `public_preservation`; and contain nonempty
`evidence_references` as public HTTPS URLs without credentials, query tokens or
fragments. Keep the underlying review evidence with this decision. The tool does
not produce an approved decision automatically or infer clearance from public
source visibility. The source country must agree with the registry. Restricted
sources and the separate private AU/NSW retention route cannot be published by
this command.

Only package v2 with a complete observed attachment census is eligible. Local
cold restoration precedes upload, and anonymous cold restoration precedes index
promotion. Original package status fields describe the capture candidate; public
delivery is recorded separately by the exact revision receipt. No package or
publication receipt asserts national completeness.

Receipts are created exclusively: an existing receipt is not overwritten. If
remote verification succeeds but saving the local receipt fails, the command
reports the verified result separately from the local failure. Failed network
operations report unconfirmed remote state rather than claiming no upload took
place; retry from the same candidate to reconcile immutable remote bytes. Error
output contains exception classes, not private source data or signed URLs.

Run the critical transport mutations with:

```sh
uv run --locked python tools/mutation_foi_delivery.py
```

The reviewed Alaveteli directory overlay preserves the original donor seed bytes.
`config/foi/directory-review.json` binds the saved directory observations to a
SHA-256 digest and explicit country/source mappings. The catalogue now includes
30 sources. The distinct Argentina host remains separate from its historical
seed until their relationship is verified. Romania's directory HTTP spelling is
recorded without changing the registered HTTPS origin. An absent directory listing
is not evidence that a country has no FOI source.

`discovery-review.jsonl` records the directory's limited scope for all 251 entities.
It is included in the immutable manifest, with broader discovery still required.
The geographic denominator remains 250 countries/areas/project extensions plus
one separately counted supranational entity; it is not 250 sovereign countries.
