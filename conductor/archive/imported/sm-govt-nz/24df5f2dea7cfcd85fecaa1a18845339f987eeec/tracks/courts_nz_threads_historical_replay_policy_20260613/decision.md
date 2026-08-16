# Decision - Threads Historical Replay Policy

## Recommendation
Do not replay the full historical Courts of New Zealand archive to Threads for
the MVP.

## Rationale
Threads historical replay would publish archival records as current Threads
posts. The current official Threads API publishing flow supports creating and
publishing posts, but the project has no supported backdate field for preserving
the original publication time as the platform timestamp. That makes a 738-record
replay noisy and potentially misleading even if each post includes the original
date in the text.

## Approved MVP Behavior
- Use Threads for ongoing-forward mirroring only after credentials, adapter
  launch, and controlled live-post review are complete.
- Preserve the full historical corpus through GitHub, Hugging Face, Zenodo, and
  the Bluesky mirror replay lane.
- If Threads historical replay is reopened later, prefer a limited sampled
  replay or a pinned corpus link rather than full-feed replay.

## Guardrail
Threads archive replay remains disabled in `config.json` unless a later
implementation track explicitly changes this decision.
