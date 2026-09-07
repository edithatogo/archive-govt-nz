# Strict capture binding validation

The complete locked harness at
`f0bf7db902b29fa6c0818edbb8bf731c407bbe6f` completed with exit 0:
5,598 tests passed, all configured follow-on gates passed, CAS throughput
683.41 MB/s exceeded the 25 MB/s minimum, and the 112-component SBOM validated.

Independent review cleared both follow-up malformed-record findings with 117
focused tests, including the real local HTTPX redirect/gzip path. Original and
final URL digest binding, decoded-body/CAS reconciliation, unique Content-Type
and exact outer WARC framing are enforced. Legacy unbound receipts remain
preserved and cannot be silently upgraded into capture-time evidence.

PR #421 review thread `PRRT_kwDOTo2MOM6fyBeB` was resolved with the fix and
verification references. Protected auto-merge was enabled for this exact head;
at that observation the PR remained open while hosted checks ran. Auto-merge
configuration is not proof of a merged result. No bypass was requested.
