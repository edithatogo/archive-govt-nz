# Fresh durable recovery after operational continuation

At 2026-09-07T02:47:20Z the repository-native recovery drill reconstructed all
552 objects from a newly downloaded, immutable public HF package. It reported
zero mismatches and zero schema findings. Every restored input file remained
byte-identical. No Actions artifact, Hub cache, token, publication, or remote
mutation was used. Source bytes remain in ignored scratch, outside Git.

The exact committed parent reference, its later rights authority, the package's
71,776,346-byte size and SHA-256, all inner object fixity, roots and source scope
were verified before reconstruction. `receipt.json` binds the exact software
revision, package/revision, restored file hashes, execution times and probe hash.
This observation occurs after successful operational runs 33800180992,
33968609350 and 34076094680, satisfying the separate post-operation durable
recovery ordering requirement. It does not claim durable publication of the
904-record child state; the approved published package contains 552 records.

The first download received HTTP429 before restoration. After backoff, the
second download and inner verification passed, but the probe selected a modern
continuation-root helper requiring a harvest receipt absent from this older
durable parent. The corrected probe compares every restored file hash instead;
all native authority, package and reconstruction verifiers remain unchanged.
Both unsuccessful attempts are preserved in `download-attempt-01.json` and
`download-attempt-02.json`. A subsequent fresh download and reconstruction passed.

Reproduce in an isolated checkout at the exact receipt software commit, with
the retained probe placed at this relative path:

```sh
uv run --locked python evidence/migrations/corpus-legislation-nz/durable-recovery-after-operation20260907/verify.py.txt
```

The probe refuses another HEAD, optimized Python and Actions context. Its output
receipt is exclusive; use a fresh checkout/output directory for a repeat. This
is a real-state read-only recovery observation, not a new full harness run.
