# Bronze artifact archive

The archiver consumes retained GitHub Actions artifacts without fetching the source websites again. It publishes one additive batch per artifact and reviewed routing policy. The first route is government-web in the public, ungated `edithatogo/archive-govt-nz-global` dataset. The repository publication identity map reserves the social-media dataset for the social-media producer.

Run the CLI from the repository root using the locked Python 3.15.1 environment and existing GitHub read and Hugging Face dataset write authentication.

```sh
.venv/bin/python -m tools.bronze_archiver --run 41305833615
```

Repeat `--run` to process specific successful main-branch runs. With no arguments the CLI enumerates retained artifacts by registered name. On main the Bronze artifact archive workflow exposes the same manual dispatch and consumes successful scheduled or manual multi-source producer runs. It uses the existing HF_TOKEN repository secret and Actions read permission.

## Admission and recovery

Register a producer workflow, source set, Hub dataset, exact URLs and reviewed response hashes in `config/bronze/archive-routes.json`. The input contract is the multi-source capture, archive-fixity and replay receipts plus the original CAS and WARC members. New hashes default to held. Register other artifact layouts through their existing source-specific writers or qualify a compatible export first.

The CLI checks GitHub's ZIP digest, checks the producer receipts, and binds the WARC response to the source URL and CAS hash. The manifest accounts for every configured target. Each eligible capture links to its unchanged body, WARC, copyright policy and attribution. Held bodies and their WARC bytes are excluded. Keep the source-specific licence and the raw-capture review decision separate from the project code licence.

The Hub manifest, content-addressed objects and WARC files are committed against the observed parent. Existing paths must have identical native file identities. One anonymous readback checks all batch members at the commit revision. A separate immutable verification receipt lets subsequent runs skip the batch even from a new runner. If the data commit exists without its receipt, rerun the same command while the source artifact is retained. The CLI reconciles the existing content before finishing verification. A parent conflict fails the affected batch and can be resumed with the same input.

## First published batch

Successful producer run 41305833615, artifact 13082423185, captured two homepages. The eligible DIA HTML and its WARC were preserved; the Govt.nz capture had an inline third-party logo and was recorded as held. A second invocation reported already_verified. [Pinned manifest](https://huggingface.co/datasets/edithatogo/archive-govt-nz-global/blob/33d3de7dcb421226d75b1dad1bcf4c799204a0f1/bronze/batches/government-web/13082423185/0818fc6bd7344322e21478950f4af3987359bae9495e7caa26c26339e0b5cec6/manifest.json)

### Held government-web review, 2 November 2026

This chat owns the bounded ten-artifact rights review and additive publication
in `/Volumes/PortableSSD/CodexWorkData/legal-coverage-20261031/recovery-checkout-20261101`,
branch `codex/bronze-held-review-20261102`. The native scope is the ten existing
government-web source artifacts and their new policy-bound batches in
`edithatogo/archive-govt-nz-global`. Previous batch receipts remain immutable.

The ten exact DIA HTML versions were reviewed against
https://www.dia.govt.nz/Copyright. They contain linked image assets rather than
embedded SVG or data images. Original HTML and its bound WARC qualify under
CC BY 4.0 with written Crown/DIA attribution. Linked assets are excluded.
All ten Govt.nz HTML versions embed the Shielded logo. The exceptions at
https://www.govt.nz/about/the-govt-nz-website/using-this-website/copyright-and-attribution/
continue to require holding those original bytes.

All ten source ZIP digests matched GitHub metadata. One offline admission pass
confirmed each batch produces one held Govt.nz record and one archived DIA
record with matching body and WARC checksums. Existing regression evidence from
PR #851 is reused. Each published batch receives its normal single anonymous
readback and durable verification receipt. Exact inventory and native results
are retained locally in `build/bronze-held-review/inventory.json` and
`build/bronze-held-review/publication.jsonl`.
