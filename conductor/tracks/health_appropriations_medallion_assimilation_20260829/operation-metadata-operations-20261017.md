# Source-regenerated metadata operations

Two typed CLI commands expose the existing operation-context Platinum v5 API:
`health-appropriations-build-operation-context-metadata` and
`health-appropriations-verify-operation-context-metadata`. Both accept
`--input-spec`, `--source-root`, `--gold-package`, `--gold-manifest-sha256` and
`--output-dir`; verification also requires `--manifest-sha256`. The input spec
is the existing closed five-profile operation-context JSON contract. No Fiscal
or Budget inputs are required for this standalone profile.

Build defaults to dry-run and still regenerates Gold/metadata from trusted Bronze
inputs before returning success. `--write` uses the existing immutable-output
guard and performs source-regenerated post-write verification. Repeated builds
use fresh directories; existing or partial output is refused, not overwritten.
Verification binds independent Gold and metadata pins and compares reconstructed
products, not merely a candidate's self-consistent manifest.

The read-only MCP tool is
`health_appropriations_verify_operation_context_metadata`, with the same six
verification fields, strict schema, v5/packages1 receipt and source-regenerated
verification scope. The shared adapter only reads the existing spec and invokes
qualified metadata APIs. Existing v3/v4 CLI/MCP definitions remain unchanged.
Rights stay not_evaluated and publication not_performed; no schedule activation,
acquisition, renderer, formula or analytical join is introduced.

The initial three missing-command failures were preserved; the implemented real
product contracts passed, then76 related/refusal/legacy/MCP tests passed with
two RDFLib deprecation warnings. Ruff/format/type and Conductor checks pass.
The native CLI/MCP proof passed on e876eaf3; independent readback covered63files
and the9metadata outputs matched the PR705 baseline exactly. The initial full
run timed out at900seconds with one unidentified failure marker; its cache
selection passed56tests without identifying that failure. An unchanged-source
four-worker recovery passed7901tests and every stage through licence inventory,
then stopped on a receipt-label false positive in the credential scan. The
redundant aggregate label is now neutral and accurate; original results/logSHA
and history are retained, with no scanner/rule/baseline change. Affected scan
recovery, previously unrun SBOM and hosted delivery remain pending. This
checkpoint does not close the track or phase.
