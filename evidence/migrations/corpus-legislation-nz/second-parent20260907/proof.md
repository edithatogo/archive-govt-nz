# Independent second-parent continuation proof

**Verified:** run [34076094680](https://github.com/edithatogo/archive-govt-nz/actions/runs/34076094680),
attempt 1, batch `ordered-second-parent-20260907`, on merged PR414 software
`4b1764bbdc275d400204e6974bcde621a8f8d037`. The hosted job completed successfully
in 9m23s. Independent local verification also passed. No retry, dispatch, workflow
change, registry/track update, publication or remote mutation was performed by
this verifier. Parent's synthetic-tool correction `ccdd40bf` and final assurance
remain separate; this is a bounded operational proof, not programme completion.

## Exact outcome

| Check | Independently verified result |
| --- | --- |
| Selected input | Committed `config/legislation/parents/ordered-500-33968609350.json`; artifact 9970365066 from run 33968609350. Authenticated metadata, ZIP digest, roots, seal and native parent verification pass. |
| Input corpus | 904 manifest records and 904 CAS objects. |
| No-write preflight | Hosted restoration lineage embeds the exact selected reference. Its reconstructed restored-state file hashes equal both preflight snapshots. Successful preflight completed before harvest started. |
| Exact accounting | All 500 unique reviewed work IDs have exactly one outcome: **500 unchanged_revalidated**. Zero newly/changed preserved, skipped, unavailable, partial or failed; zero retries. |
| Child corpus | **904 records / 904 CAS objects**. Every input CAS object remains byte-identical. State/CAS byte and object budgets pass. |
| Reconciliation/checkpoint | Local reconciliation agrees with hosted reconciliation apart from evaluation timestamp: 500 works, 852 scoped records, zero mismatches. The completed checkpoint includes this exact batch. |
| Seal/lineage | Complete child continuation seal binds current roots, parent lineage, source, run attempt and software commit. Native schema and semantic verification pass. |
| Output as parent | Derived evidence-only output reference passes schema, fresh hosted metadata checks and native verification against the actual child ZIP. No third cycle was dispatched. |
| Negative control | Corrupting a copied CAS object fails with `object_sha256`. Original scratch state remains unchanged after all verification/reconciliation. |

The CAS root, inventory root and semantic manifest root remain unchanged across
this revalidation. The checkpoint and manifest file byte digests differ; their
exact values are retained in `outcome.json` and `output-parent-reference.json`.
Unchanged corpus content does not mean the new checkpoint or execution receipts
are byte-identical to their parent.

## Reusable output identity

- Artifact: **10002260735**, `legislation-exact-inventory-state-34076094680-1`.
- ZIP: 10,634,093 bytes; SHA-256
  `d9c9b35c29b640cdd705e5e46d66ac7f9c75727c8cd527ba48514e826f314954`.
- Expiry observed: `2026-12-06T02:22:57Z`.
- Seal SHA-256:
  `d7d82e7db94ff7528ae2354bce4c715e0cf7515816f400f3a431e5909af74579`.
- Independent outcome receipt SHA-256:
  `841adade6e6edb0a9e414c0357b6477da648f5cd295bd844145bf869211a36e2`.

`output-parent-reference.json` is a verified handoff artifact within this evidence
directory. It has not been installed into the operational configuration or used
to authorize another execution. Actions retention is not a new durable HF
publication or independent long-term recovery guarantee.

## Reproduction and evidence boundaries

In an isolated checkout at the exact software commit above, place the retained
probe at this relative location and run from repository root:

```sh
uv run --locked python evidence/migrations/corpus-legislation-nz/second-parent20260907/verify.py.txt
```

The probe requires existing `gh` read authorization and refuses a different local
HEAD or an Actions environment. It creates only scoped receipts and ignored
`.tmp/second-parent-*` payload scratch. ZIP members are checked for bounds,
duplicates and unsafe paths/types before extraction. No credentials, signed
URLs, raw command stderr or source payloads are committed. No full harness or
package reproducibility build was run; `uv sync --locked` only prepared the
normal local environment.

`artifact-downloads.json` records exact hosted ZIP metadata and every downloaded
member's original byte size/hash for all four child-run artifacts plus the
parent ZIP. Saved JSON receipt projections may have normalized whitespace;
original byte hashes remain in that download inventory. `SHA256.json` binds the
retained probe and JSON proof files. `hosted-readback.json` preserves step times
and conclusions; the proof does not infer ordering from workflow configuration
alone. The code recomputes corpus roots and accounting instead of adopting
labels in prior reports.

No failed hosted attempt was observed: the selected run completed on attempt 1.
The verifier completed successfully on its first full invocation. Its deliberate
in-memory corruption probe is the only rejected control. Probe syntax, all
indexed file digests and the unchanged repository-policy targeted secret scan
were checked; no secret candidates were found. The full programme, track
lifecycle, subsequent corrective head and final integrated assurance remain
parent-owned.
