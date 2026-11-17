# SOC06 — socioeconomic publication, source-state views and freshness

Status: not implemented or deployed. Depends on accepted SOC04/SOC05 output, existing publication infrastructure and the retained P9 owner. No new deployment authority or controller is created.

## Required source-state distinction

Every source/metric must show separate evidence for: (1) already archived and byte-verified, (2) archived but not normalised, (3) normalised but not join-qualified, (4) joined but not published, (5) live at the verified HF revision, (6) planned/unknown/held. A missing connector listing is unknown, not absent; a derived Parquet filename is not proof of source provenance. This implements the recommendation to distinguish existing, proposed, joined and future layers.

## Executable tasks

- [ ] Add a public-safe source coverage catalogue and provenance drawer through the existing dashboard owner; do not create a separate dashboard or competing HF dataset.
- [ ] Bind observation period, boundary vintage, source publication time, capture time, validation time and deployed revision independently. Display explicit indicator age and preliminary/final result status.
- [ ] Expose qualified socioeconomic profiles beside electoral outcomes with accessible table alternatives, appropriate units/universes, missingness and ecological-caution labels.
- [ ] Supply original-source citations, methodology, source/lookup/code hashes and validated CSV/Parquet/Arrow exports using existing tooling; compare served data against the same approved release manifest.
- [ ] Add schema/source drift checks and bounded refresh proposals only after source access and scheduled-operation authority are accepted. Preserve prior releases and rollback; no automatic re-capture merely because a timer fires.
- [ ] Verify real desktop/mobile/keyboard behaviour, failed/missing data states, export parity and actual served HF bytes/revision after a separately authorised publication operation.

## Admission versus release

A code/document PR may be integrated only after native/runtime/full-harness/current-head checks and existing-owner acceptance. It does not require an unauthorised production publication to be mergeable. A later public-data/outcome-completion claim requires actual served parity, authorised rights/destination and rollback evidence. Both gates remain binding.

## Handoff prompt

As the existing P9 owner, connect one admitted socioeconomic Gold output to the current Space with verified source-state badges, dates, coverage and exports. Keep unqualified or absent data visibly unavailable. Only perform a public write under separate current authority; otherwise prepare the reproducible bundle and leave publication held.
