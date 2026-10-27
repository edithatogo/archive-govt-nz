# Evidence — 26 October 2026

Parent [#778](https://github.com/edithatogo/archive-govt-nz/issues/778); implementation start f149f26e. All eligible Parliament outputs must use the public, ungated existing dataset `edithatogo/archive-govt-nz-global`. No private destination or repository creation fallback is implemented.

## Native source qualification

- Current Parliament and selectcommittees hosts allow crawling. Legacy `www3.parliament.nz` generic robots policy denies all paths (SHA256 `e19bf175c5b805494a9bfcf76e5a80483499f01e74c48bb4fe45498c5668b21a`). The worker respects that denial.
- Public [all-Parliaments report UI](https://selectcommittees.parliament.nz/reports?Tab=All) and its public POST `/api/data/search` report 10,970 entries. A count is an observed index population, not unique originals captured.
- Page 1097 contains ten entries with absent attachments and year-0001 placeholder dates. Preserve exact raw API bytes; label these metadata-only/unknown-date, never fabricate files or dates. Raw response SHA256 `583b1163e06bc049fc037eed5d59d1fe4a98147c72ee170bccfe1365d4c59090`, 4,556 bytes. This tail page is not proof of chronological oldest coverage.
- [Current copyright statement](https://www.parliament.nz/Copyright), updated 25 August 2025: committee reports public domain; Clerk/Parliamentary Service material CC-BY4; submissions and most committee advice excluded from the general permission. Those collections remain rights-pending.
- Legacy evidence and current submissions/advice totals differ in population and cannot be summed or asserted as reconciled unique coverage. Petitions, papers, questions, Library research and procedural records require their own source contracts; public navigation commonly points to the denied legacy host. Media remains deferred.

## Public remote evidence

Anonymous SDK target readback: `private=false`, `gated=false`. Retained write identity: `edithatogo`; no credentials copied or committed. Originals and manifests were downloaded anonymously from pinned revisions and independently SHA256 checked.

| Pilot | Batch | Remote revision | Evidence scope |
| --- | --- | --- | --- |
| Initial report | f6e696570f75200e4b84f0aeabc297c2cb2455afd8762b5fdbb00322564fb485 | 374152c18f5e82e6e00d52487d8b0caf438f04cc | 210,975-byte, seven-page PDF; original hash 1ca0142d259c0aa57950b43774e0b0e4a68e72ddd34595851c9d2dde28a2aeaf |
| Canonical report identity | 704e105432c595c3c931389b344c8b721041997c3d885b11f259bea38440d989 | 02159e75d67e2025ed99e565fb5dbde01a31a728 | API-based identity; preserves initial pilot history |
| Bounded historical manual worker | 25c70191ddbae03b43fa4b92e2a94720274f32cf9de54073a74f6dd8e7648280 | c82520171de5b5b06182d2d2568f4238faac47f8 | 10 discovered, 10 captured, 0 failed, 2,775,500 payload bytes, remotely verified |

[Public Parliament batches](https://huggingface.co/datasets/edithatogo/archive-govt-nz-global/tree/main/parliament). These pilots overlap; do not add pilot counts as unique coverage. Existing Hansard source archive metadata is public but download gated; the new target requires ungated anonymous access.

## Local implementation and limits

Repo-selected `.venv/bin/python` verified 3.15.1. Task-owned environment/build/temp moved to PortableSSD after internal disk exhaustion; source worktree unchanged. SQLite/CAS and OS file locks preserve cursors, immutable observations, interrupted segments and uploaded/unverified batches. Reports use the qualified public API; exact raw API responses accompany v2 payloads. V1 pilots remain readable. Hash-bound eligibility decisions precede additive commits with parent revision conflict protection; every object must pass anonymous pinned remote download before verification.

74 focused synthetic tests passed; updated provenance regression passed separately. Mocked HTTP/Hub tests cover crash/restart, robots denial, cooldown, bounds, visibility, integrity, unknown upload outcome and stale checkpoints. Ruff passed; type error corrected and whole-project type gate passed. Full `./scripts/validate.sh`: 8,423 passed, 14 capability skips, 97% aggregate branch-aware coverage; schemas 83/83 and parity 9/9 passed. All repository mutation stages, dependency audit, licence inventory, corrected secret scan and strict SBOM validation (118 components) passed. The full command stopped at a fictional negative-test credential URL; annotated that exact fixture and resumed affected scan plus SBOM through `uv run --locked`. No hosted CI, natural scheduled execution, complete mixed submission/advice/report pilot, full historical reconciliation, or broad archive coverage claimed.

Acquisition defaults: 100 records, 250 MiB, 900 seconds, 64 MiB/file, 1 GiB spool (manual qualification used 8 GiB). Publication is a separate checkpointed stage; SDK commit/anonymous verification is not proven to finish within acquisition's 900-second deadline. Shared state root enforces one owner/request budget; extra streams must reuse it. Historical offsets can drift; periodic full reconciliation remains required before completion claims. No spool deletion policy is qualified. Two-hour chat heartbeat `public-parliament-archive-continuation` is ACTIVE, gated on required assurance before scaling; natural execution remains unverified.

V2 metadata-only tail batch `158ef5274d09fb530cd346066693be9ddbd7665d423a5a30d85d547bbeb9800a` published at revision `f4bb4d6b924e865b5fb58331e1bf42bc20dcc19b`; exact 4,556-byte raw API response anonymously downloaded and verified. Ten missing attachments remain metadata-only; this publication adds no report-file coverage.

Review mutation evidence: four isolated mutants (public visibility, anonymous download, remote fixity, robots policy) killed; integrated into the existing Medallion mutation runner. Existing full-harness mutation stages also passed. No mutation ran against production source or real Hub writes.

Final review fixes: f18c3ee7 implementation, b326ae87 four policy mutation guards. Whole-suite result predates only the mutation-registration and fixture-comment changes; focused mutations, format/lint/types, schema, exact affected test and resumed supply-chain evidence cover those bounded edits. Anonymous final dataset readback: private=false, gated=false at f4bb4d6b924e865b5fb58331e1bf42bc20dcc19b. No natural scheduler run claimed.
