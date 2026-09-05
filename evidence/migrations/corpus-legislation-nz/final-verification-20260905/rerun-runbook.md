# Repeating the terminal verification after Prompt 20

This is an executable audit procedure, not a completion claim. The September 5
preparatory results must not be substituted for verification after Prompt 20.
Start from a clean issue worktree at the exact integrated candidate, record
`git rev-parse HEAD`, and bind the passing Prompt 20 receipt and hosted check SHAs.
Do not move the candidate while evaluating. Preserve this preparation and write a
new dated execution subdirectory for the terminal run, including failed attempts.

Use `acceptance-plan.json` as the requirement checklist: independently evaluate
all 16 criteria and ten false-completion probes. Record four separate dimensions.
A missing proof, failed check, or unexplained mismatch prevents overall completion.
The commands below reproduce the primary operational and external checks already
performed. They do not replace the remaining checks listed at the end.

## Interpreter and transient workspace

Use the repository's lock-governed Python environment. Record Python, platform,
Git, `gh`, lockfile hash, and verification tool hashes. The examples assume its
Python is accessible as `python`; do not silently use a different environment.
Create a new private temporary directory with `mktemp -d` and record its exact
path. Keep downloads, extracted state and cloned repositories there only. Do not
commit a canonical payload, credential, signed URL, or raw authentication header.
Use a separate new output directory beneath this dated evidence directory for
public receipts, bounded logs, and response hashes.

## Primary operational artifact retrieval

Execute these read-only requests and retain their exact response hashes. Store
only public selected fields in committed readbacks; omit signed redirect URLs.

```sh
gh api repos/edithatogo/archive-govt-nz/actions/runs/33800180992
gh api repos/edithatogo/archive-govt-nz/actions/runs/33800180992/jobs
gh api repos/edithatogo/archive-govt-nz/actions/runs/33800180992/artifacts
```

Write each response to a named JSON file in the temporary directory. Independently
retrieve each artifact using `gh api` and binary output redirection:

```sh
gh api repos/edithatogo/archive-govt-nz/actions/artifacts/9911100379/zip
gh api repos/edithatogo/archive-govt-nz/actions/artifacts/9911101072/zip
gh api repos/edithatogo/archive-govt-nz/actions/artifacts/9910743836/zip
```

These correspond to state, attempt and parent ZIPs. Before unpacking, compare
`len(raw)` with API `size_in_bytes` and `"sha256:" + hashlib.sha256(raw).hexdigest()`
with API `digest` for all three; require `expired == false`. Do not infer content
integrity from a successful workflow conclusion. Require run and all job
conclusions `success`, run ID 33800180992, attempt 1, branch `main`, workflow
`.github/workflows/exact-inventory.yml`, and source software commit
`95d5e0959158df3e5f816b012b66049135ff3d54`.

## Native state, accounting, and continuation verification

From the candidate repository root, add its root and `src` to Python's import
path. Run the following against the newly downloaded state bytes. `state_zip`
is the exact transient path, and `run` is the newly fetched run response.

```python
import hashlib
import json
from tools import legislation_parent_state as p

sha = lambda raw: hashlib.sha256(raw).hexdigest()
files = p.unpack(state_zip.read_bytes())
roots = p.state_roots(files)
seal = json.loads(files[p.SEAL])
lineage = json.loads(files[p.LINEAGE])
harvest = json.loads(files["receipts/harvest.json"])
manifest = json.loads(files["manifest.json"])
checkpoint = json.loads(files["checkpoint.json"])
assert roots == seal["roots"]
p.check_lineage(lineage)
assert sha(files[p.LINEAGE]) == seal["parent_lineage_sha256"]
assert seal["context"] == lineage["context"]
assert run["head_sha"] == seal["context"]["software_commit"]
assert harvest["run_identity"] == str(run["id"])
assert harvest["output_manifest_root"] == roots["manifest_sha256"]
assert harvest["output_checkpoint_root"] == roots["checkpoint_file_sha256"]
cas = {name.split("/")[-1]: raw for name, raw in files.items()
       if name.startswith("cas/")}
assert len(cas) == 904
assert all(sha(raw) == digest for digest, raw in cas.items())
assert len(manifest["records"]) == 904
assert len(checkpoint["processed_work_ids"]) == 552
assert harvest["works_attempted"] == 500
assert harvest["changed_preserved"] == 352
assert harvest["unchanged_revalidated"] == 148
assert all(harvest[key] == 0 for key in
           ["failed", "partial", "unavailable", "already_processed_skipped"])
seed = (p.ROOT / "seeds/reviewed/historical-work-ids-0001.txt").read_bytes()
assert sha(seed) == seal["source"]["seed_sha256"]
assert set(seed.decode().splitlines()) == {
    work["work_id"] for work in harvest["works"]}
context = seal["context"]
reference = {
    "roots": roots,
    "lineage_sha256": sha(files[p.SEAL]),
    "state_schemas": seal["state_schemas"],
    "source": seal["source"],
    "repository": context["repository"],
    "run": {"head_branch": context["branch"], "id": context["run_id"],
            "run_attempt": context["run_attempt"],
            "head_sha": context["software_commit"]},
    "workflow": {"path": context["workflow"]},
}
p.verify_parent(files, reference)
# Negative control: alter a copy in memory, never the source artifact.
mutated = dict(files)
name = next(name for name in mutated if name.startswith("cas/"))
mutated[name] += b"x"
try:
    p.state_roots(mutated)
except p.v.VerificationError as exc:
    assert str(exc) == "object_sha256"
else:
    raise AssertionError("Tampered CAS was accepted")
```

`state_roots` calls native `target_state` reconciliation, validates checkpoint and
harvest accounting, enforces the state namespace, checks record/CAS identities,
and recomputes semantic manifest, inventory, physical checkpoint, CAS and receipt
roots. The explicit physical CAS loop is an additional independent hash pass.
The reference is constructed only after authenticated run and artifact binding;
it demonstrates sealed-parent validity, not authorization for a new dispatch.

After native safe unpacking, write only its validated file mapping beneath the
new temporary state directory. Then rerun the existing batch reconciler:

```sh
python tools/reconcile_one_legislation_batch.py \
  --batch-id prompt13-500-verification-20260904-identity-fix \
  --batch-path seeds/reviewed/historical-work-ids-0001.txt \
  --expected-batch-sha256 59923176fa34796d7673a20b880af9abe5520fe484595edb220f2bbc0e3b33e7 \
  --manifest-path TEMP_STATE/manifest.json \
  --checkpoint-path TEMP_STATE/checkpoint.json \
  --cas-path TEMP_STATE/cas \
  --receipt-path NEW_EVIDENCE/reconciliation.json
```

Replace the two uppercase path placeholders with the actual private temporary
state and new evidence paths. Require exit 0, `status: passed`, zero mismatches,
500 reconciled work IDs, and 852 selected records. Keep 904 cumulative records
separate from the 852 records selected by this 500-work scope. No result here
proves public release of the 904-record continuation.

## Donor identity and public bundle restoration

Retrieve and hash these responses independently:

```sh
gh api repos/edithatogo/corpus-legislation-nz
gh api repos/edithatogo/corpus-legislation-nz/git/ref/heads/main
gh api repos/edithatogo/corpus-legislation-nz/git/ref/tags/migration-final-20260821
gh api repos/edithatogo/corpus-legislation-nz/git/tags/cdd6a397a96773c06519e2e86bbe7a606b26bd58
gh api repos/edithatogo/archive-govt-nz/releases/tags/corpus-legislation-nz-final-archive-20260903
```

Require archived true; distinguish redirect head
`905f9e07c17af9d9d25dbe2b1c052fb8a290a4e3` from operational final head
`b40587f1b1aec7356a0f623916fcc8212397d283`. Require the annotated tag object to
resolve to the operational head. Read `README.md` through GitHub contents API
with `?ref=` pinned to the observed redirect head, decode its base64 bytes, hash
and inspect the target redirect. Never unarchive or modify the donor.

Select the public release's `corpus-legislation-nz-full-20260826.bundle` asset.
Download its `browser_download_url` without authentication using
`urllib.request.urlopen`; require HTTP 200 and API size/digest equality.
The prepared observation was 2,365,303 bytes and SHA-256
`f125f91b06264a97e59f65fac47878a74d646c915f12c0b05841c1550ec741c2`.
Clone the newly downloaded bundle into a fresh private temporary bare repository:

```sh
git clone --bare TEMP_BUNDLE TEMP_RESTORE.git
git -C TEMP_RESTORE.git fsck --full
git -C TEMP_RESTORE.git rev-parse refs/heads/main
```

Retain exit codes and bounded output. Require fsck success and operational final
head. Historical dangling commits are not corruption; preserve their diagnostic
output rather than claiming no diagnostics. The original bundle predates the
redirect/tag; prove those separately from live readbacks.

## Zenodo and cutover release readback

Read `https://zenodo.org/api/records/20592540` anonymously and hash the exact
response bytes. Check `doi`, `conceptdoi`, `conceptrecid`, record ID, title,
version, publication date, licence, related identifiers and every file entry.
Expected relationship is version `10.5281/zenodo.20592540` and concept
`10.5281/zenodo.20592539`. Do not alter the record or mint a DOI.

For every API file, anonymously fetch `links.self`, verify HTTP 200, size, and
`"md5:" + hashlib.md5(raw).hexdigest()` against its API checksum. MD5 is used
solely to compare the publisher's supplied checksum. Also calculate SHA-256.
Parse the downloaded `nz-legislation-corpus-2026.SHA256SUMS.txt` and compare every
named entry with SHA-256 of its freshly fetched bytes. Payloads may remain in
memory only; preserve the computed verification receipt, not archive payloads.

Read and hash the public cutover release:

```sh
gh api repos/edithatogo/archive-govt-nz/releases/tags/legislation-cutover-v1.0.0
```

Retain the exact body in the new evidence directory. Inspect the dated addendum
and original wording: cycle 1 recovery 32625612739, cycle 2 recovery 32626113799.
String presence is only a first check: verify the supporting harvest,
reconciliation and recovery chains from the primary run URLs identified by
`cutover-release-provenance/cutover-release-provenance-correction.json`.

## Recovery, remaining criteria, and completion gates

Rehash all `attempt_receipts`, `durable_stage_receipts` and `authority_receipt`
paths named in `durable-recovery/independent-recovery-summary-20260903.json`.
Load both attempt receipts and independently compare package and restored state
objects. Check fresh direct download/workspace, no Actions/cache source, no-write
input/output tree equality, zero reconstruction or unexplained internal
mismatches, and workspace destruction evidence. Preserve original reconciliation
exit 1 and its explained external metadata handoff. Bind the new Prompt 15
monthly comparison that resolves that exact selected-552 metadata handoff;
do not silently recast the historical failed command as successful.

Before terminal closeout, execute the remaining acceptance-plan checks:

- Donor lineage: compare imported tree/commit disposition with the newly restored
  donor bundle; inspect all 15 post-baseline commits and excluded paths.
- Donor state and merge: compare original 500 donor object hashes and 52 target
  inputs with independently verified durable 552-state, preserving every
  conflict disposition. Obtain fresh authoritative bytes where practical.
- Seed: recalculate byte count, exact SHA-256, LF-only 500 unique nonblank lines,
  canonical ordering, and registry source/run/commit relationship.
- Lane separation and restoration: inspect integrated exact-inventory and
  scheduled-discovery workflows, typed contracts, scope budgets and concurrency;
  bind the focused negative tests in the current P20 validation.
- Durable custody: revalidate exact public HF package authority and rights;
  do not use the operational Actions artifact as its source of truth.
- Historical coverage: recompute 68 declared batch counts summing 33,693 and
  explicitly distinguish declarations from present raw candidate bytes,
  records, reviewed work scope, and legislative completeness.
- HF: verify all registered roles and current revision-pinned card, rights,
  metadata and package readbacks; bind the selected-552 monthly comparison.
- Evidence hierarchy: use a superseding index and evaluation, validate exact
  referenced hashes and active proof eligibility, and run negative controls for
  invalidated receipts, public claims and changed content. Preserve old outputs.
- Integrated assurance: inspect P20's exact candidate, full native harness,
  meaningful mutation/coverage/security/schema results, all hosted required
  checks and current ruleset enforcement. Identify any bypass explicitly.

For each of the ten probes in `acceptance-plan.json`, record the actual check,
its result and evidence hash. A prose intention to reject false completion is
not a passed probe. The terminal report must identify every criterion separately,
name any defects and specialist owner, and derive four independent statuses.
Do not create new feature implementations inside Prompt 21.

## Cleanup and evidence closeout

First verify all committed outputs are only receipts, metadata and logs, and
rehash their references. Remove only the exact temporary ZIPs, extracted state,
and newly created bare repository owned by this attempt, using Python
`Path.unlink()`/`shutil.rmtree()` after verifying their parent is the recorded
private temporary directory. Do not use a glob or delete another agent's path.
Record cleanup completion and retain failure logs. Finally run the repository
validation harness and required exact-head hosted checks before opening/merging
the evidence PR. Never rewrite the original preparatory or historical evidence.
