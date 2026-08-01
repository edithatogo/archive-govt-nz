# Track 11: Ministry of Health discovery

Status: `[~]` active, metadata-only discovery.

Scope: enumerate Ministry of Health CKAN datasets and resource metadata from
the official catalogue. Payload capture, transformation, and publication are
explicitly out of scope until a later approved phase.

## Gates

- official HTTPS catalogue only;
- bounded pagination, retries, and response size;
- preserve identifiers, timestamps, counts, and hashes;
- fail closed on protocol or reconciliation errors;
- no credentials, payload bodies, or publication.
