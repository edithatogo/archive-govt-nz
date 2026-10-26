# MoSCoW requirements

## Must

- M1: Discover released public submissions, supplementary attachments, official advice, reports and business-item context; retain stable source IDs, Parliament, committee, dates and source relationships. Accept when a completed business-item pilot accounts for every discovered record and attachment outcome.
- M2: Reconcile legacy/new hosts, overlapping indexes, filters and pagination; retain raw discovery evidence and coverage limits. Accept when duplicate and moving-boundary fixtures pass and source scopes are explicitly documented.
- M3: Stream originals through bounded temporary storage with hashes, atomic admission, immutable versions, HTTP provenance and changed/withdrawn observations. Accept when interrupted/incomplete/corrupt downloads cannot be admitted and original bytes reconstruct.
- M4: Independently checkpoint discovery, capture and publication with durable shards and leases; share throttling across lanes. Accept when crashes, duplicate delivery and competing writers recover without missing records or silent replacement.
- M5: Enforce record, byte, runtime, file and spool limits. Initial proposed first-hit run bounds: 100 records, 250 MiB or 15 minutes. Accept with boundary tests and pilot measurements; document tuned values.
- M6: Publish all eligible NZ Parliament archive outputs incrementally to the existing PUBLIC Hugging Face dataset `edithatogo/archive-govt-nz-global` (`private=false`, anonymous access required). Never select or create a private Parliament destination. Publish using additive namespaces, immutable batches, appropriate collection metadata and serialized catalogue updates. Accept only after revision-pinned independent download/hash/reconstruction, not upload response alone.
- M7: Qualify source reuse/privacy restrictions and the exact destination/write route. User approved archival/publication intent; exact target and per-source eligibility remain unresolved. No submission personal data or source payloads in Git fixtures.
- M8: Run historical backfill and overlapping recent monitoring separately; reconcile late/replaced records and older partitions. Accept with manual-run, natural-schedule, resume and failure-ledger evidence distinguished.
- M9: Report discovery, eligible, captured, failed, changed, withdrawn, rights-pending, upload and remotely verified counts separately; retain reconstructable manifests and restriction/tombstone history.
- M10: Use repo-local verified Python 3.15.1 or newest qualified 3.15 patch, existing supported components and targeted checks; run the repository harness before a PR and milestone assurance/recovery gates.

## Should

- S1: Expand petitions/responses, papers presented, questions/answers, Library research, Journals, Order Papers and daily progress through dedicated source contracts after the pilot. Each expansion requires bounded source and recovery evidence.
- S2: Reconcile Hansard and legislation coverage/identity to reuse existing implementations and deduplicate shared objects.
- S3: Produce separately versioned text/OCR and searchable Parquet shards with transformation receipts; failures must not block original capture.

## Could

- C1: Optimize large small-file populations with bounded archive containers and an offset index after measured packaging/recovery qualification.

## Won't in initial delivery

- W1: Capture private/unreleased submissions, adopt new paid infrastructure or claim complete historical coverage from index totals.
- W2: Archive hearing audio/video until endpoints, rights, volume and recovery are qualified; no automatic media activation.
- W3: Replace existing dataset cards, licences or working archive lanes wholesale; no upstream document relicensing.
