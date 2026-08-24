# Requirements: Multi-Source Capture Path Activation

## Background
`scheduled-multi-source-harvest.yml` has failed on every scheduled run since at
least 2026-08-23T12:18Z. All five matrix jobs (nz-gazette, treasury,
social-media, newsletters, government-web) exit 2 with receipt status
`not_configured`: `src/archive_govt_nz/cli.py` `capture` is an unimplemented
stub. Until this is fixed the canonical repository cannot replace the still-live
sm-govt-nz pipelines, and the Publication Hub track has no healthy upstream.

## Core requirements
1. Choose and record one disposition: implement the capture worker path behind
   the CLI stub, or re-route each matrix job to its existing working domain
   pipeline (the legislation precedent).
2. Every source set completes one scheduled cycle green with receipts.
3. Fail-closed behaviour is preserved: no silent empty-state success.
4. No publication, rights, or donor action is authorized by this track.
