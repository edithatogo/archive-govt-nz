# Independent supplementary artifact verification

Run 34075370618, attempt 1, completed all eleven supplementary jobs successfully
on reviewed PR414 head `e015a059c88e605dd43b6127d1e7a9d81d37f574`.
The local verifier independently downloaded all eleven ZIPs using authenticated
GitHub GETs. Every ZIP size and SHA-256 matched fresh hosted metadata; every
artifact was unexpired and bound to the expected run/head/name.

All eleven execution receipts match the expected schema, target commit, run,
attempt, zero exit code, publication=false, exact suite script and directory
argument convention. Their manifests exhaustively cover **113 payload files**;
every file size and SHA-256 matched. Duplicate/unexpected/missing members,
unsafe paths, nonregular members and excessive sizes fail closed. Original
execution receipt objects are embedded in the verification receipt, together
with each original receipt byte digest and each artifact ZIP digest. Logs and
ZIP payloads remain in ignored scratch; no credentials or signed URLs are saved.

The checked suites are parent-state, durable-state, seed-registry,
source-preflight, source-sets, discovery, zenodo-identity, zenodo-publication,
donor-bundle, evidence-index and release-correction. The receipt binds each suite
to its successful job ID and artifact ID. This proves hosted execution receipt
integrity; it does not claim a fresh local re-execution of mutants.

Reproduce from a repository checkout with authenticated GitHub read access:

```sh
python evidence/assurance/ordered-integration-20260907/verify-supplementary.py.txt
```

The standard-library-only verifier checks the fixed hosted target independently
of its local checkout HEAD. It uses three concurrent downloads, 120-second
request timeouts, and explicit per-artifact size/member bounds. It only makes
GET requests and creates ignored scratch plus the two supplementary JSON outputs.
`supplementary-verification-index.json` binds the exact verifier source and
verification receipt. Verification receipt SHA-256:
`ce85047cb76a2e81d32e27f3eca2744ab4d6a6ef558546f0b26cfb3786a9053c`.

The previously committed local resource/security receipts remain unchanged and
bound by `receipt-index.json`: 904 objects, zero mismatches, unchanged state,
2.01 seconds, clear alert readbacks and an active ruleset. No additional resource
run is needed for this artifact-verification supplement. Parent owns
`reproducible-builds.json`; this supplement does not modify or certify it.
Parent-reported full harness/build results are not represented as independently
executed here. At this supplement's readback, PR414 Windows remained in progress;
the other required checks were green. Overall hosted gate completion is therefore
not claimed.
