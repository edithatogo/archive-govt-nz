# Plan - Courts of New Zealand Multi-Source Archive and Dataset Pipeline

## Phase 1: Source Inventory and Access Contracts
- [x] Task: Record official Courts of New Zealand source surfaces in repo config: Bluesky, LinkedIn, inactive X archive, website/RSS, and judgments email subscription.
- [x] Task: Discover all Courts of New Zealand RSS feed URLs by parsing page-level RSS links and site sections for judgments, announcements, speeches, reports, and daily lists.
- [x] Task: Confirm LinkedIn access method and constraints: official API if admin access exists, otherwise user-authorized browser export/capture or no-code manual seed.
- [x] Task: Confirm historical X archive method for pre-23-March-2025 `@courtsofnz` posts: public X archive, Internet Archive/CDX, browser capture, or another lawful export path.
- [x] Task: Define source health status values: healthy, degraded, auth_required, rate_limited, blocked, and unavailable.
- [x] Task: Document one adapter contract per source, including input credentials, output paths, dedupe keys, rate-limit handling, archive-only guarantee, and phase review checklist.

## Phase 2: Archive Schema and Deduplication
- [x] Task: Extend archive schema to include `source_platform`, `source_account`, `source_kind`, `captured_at`, `raw_path`, `canonical_url`, `content_hash`, and `cross_source_ids`.
- [x] Task: Add source-specific raw archive directories under `historical_archive_raw/<source>/<yyyy-mm>/`.
- [x] Task: Add normalized monthly shards under `historical_archive_normalized/<source>/<yyyy-mm>.jsonl`.
- [x] Task: Implement canonical dedupe across Bluesky, LinkedIn, RSS, email, and website pages using canonical URL plus text/media hash fallback.
- [x] Task: Ensure archive-only backfill state cannot advance `conductor/state.json` for outbound syndication.

## Phase 3: Historical Backfills
- [x] Task: Re-run Bluesky historical archive as an idempotent backfill and write a gap report.
- [x] Task: Archive inactive historical X posts for `@courtsofnz` and write a provenance/access report.
- [x] Task: Archive historical LinkedIn posts and write a provenance/access report. Tracking issue: https://github.com/edithatogo/sm-govt-nz/issues/7
  - â¸ï¸ **ARCHIVED** per user decision on 15 June 2026. LinkedIn work deferred until Instagram, Facebook, and multi-source archive pipeline are stable.
  - Blocker status is machine-checkable through `scripts/check_multisource_blockers.py`
    and the `Multi-Source Blocker Status` workflow.
- [x] Task: Archive available RSS histories and write per-feed reports.
- [x] Task: Keep all historical backfills out of live syndication targets.

## Phase 4: Ongoing Capture Pipeline
- [x] Task: Add a scheduled archive-only workflow that runs in parallel with `Syndicate`.
- [x] Task: Capture current Bluesky feed into both raw and normalized archives.
- [x] Task: Capture LinkedIn posts through the approved access method. Tracking issue: https://github.com/edithatogo/sm-govt-nz/issues/7
  - â¸ï¸ **ARCHIVED** per user decision on 15 June 2026.
  - `historical_archive_normalized/linkedin/2026-06.jsonl` contains 2 normalized manual-seed records, with raw records under `historical_archive_raw/linkedin/2026-06/`.
- [x] Task: Capture RSS feed entries with `feedparser`.
- [x] Task: Capture source website pages linked from posts/feed/email when they provide canonical judgments, speeches, reports, or announcements.
- [x] Task: Commit archive state and source health reports back to GitHub.

## Phase 5: Judgments Email Subscription Ingress
- [x] Task: Use Cloudflare Email Routing Worker as the default email ingress bridge because it has a free routing path and enough free Worker request capacity for low-volume notification capture.
- [x] Task: Keep Mailgun inbound parse as a fallback only if Cloudflare parsing/routing is insufficient and a trial or paid plan is acceptable.
- [x] Task: Keep scheduled mailbox polling through Gmail or IMAP as the final fallback if webhook-style inbound delivery is unavailable.
- [x] Task: Create a dedicated subscription address for Courts of NZ judgments of public interest notifications.
  - The active automated subscription address is
    `em4mkapmjakoh5o@upload.pipedream.net` (Pipedream Email trigger). It is
    deployed, verified with two test dispatch runs (`27624019635`,
    `27624118414`), and subscribed to all four Courts of NZ judgment lists via
    the official subscribe form on 2026-06-17.
  - Subscription confirmation was verified pending on 2026-06-21: no `Archive
    Email` repository_dispatch runs occurred between 2026-06-17 and 2026-06-21.
    The last run was `27624118414` on 2026-06-16 (a deployed test).
  - The planned permanent Cloudflare-routed address
    `courts-nz-judgments@archive.edithatogo.com` remains
    `pending_external_setup` because `edithatogo.com` is not registered.
    Domain registration is cost-bearing and requires explicit approval per the
    Cloudflare cost guardrail.
  - The active address, subscription state, and confirmation verification are
    recorded in the `active_subscription_address` field of
    `config/courts_nz_email_ingress.json`. The acceptance criterion (email
    messages can enter the repository through a documented bridge and are
    archived as raw and normalized records) is satisfied by the Pipedream,
    Cloudflare Worker, and manual dispatch routes.
- [x] Task: Store raw email payloads under `historical_archive_raw/email/<yyyy-mm>/`.
- [x] Task: Normalize email subject/body/link records into the shared archive schema.
- [x] Task: Trigger GitHub Actions with `repository_dispatch` or a scheduled polling workflow after email receipt.
- [x] Task: Add a deployable Cloudflare Email Routing Worker template and tests for dispatching received messages into GitHub.
- [x] Task: Add a manual GitHub Actions deployment workflow for the Cloudflare Email Routing Worker.

## Phase 6: Hugging Face and Zenodo Corpus Publication
- [x] Task: Define the Hugging Face dataset name, license/readme, citation, and provenance statement.
- [x] Task: Define the Zenodo deposition metadata, communities if any, citation fields, DOI/versioning policy, and provenance statement.
- [x] Task: Add `HF_TOKEN`, optional `HF_DATASET_REPO_ID`, `ZENODO_TOKEN`, and optional `ZENODO_DEPOSIT_ENDPOINT` setup requirements to the setup guide and secret schema.
- [x] Task: Publish normalized JSONL and Parquet shards to Hugging Face Datasets. Tracking issue: https://github.com/edithatogo/sm-govt-nz/issues/6
  - `HF_DATASET_REPO_ID` is no longer a blocker: when omitted, the
    `Publish Archives` workflow infers the Hugging Face namespace from
    `HF_TOKEN` and creates/updates `courts-nz-public-notices-archive`.
  - Manual publish run `27502440387` uploaded the dataset to
    https://huggingface.co/datasets/edithatogo/courts-nz-public-notices-archive
    and unauthenticated `HEAD` verification returned `200 OK`.
- [x] Task: Publish citable release snapshots to Zenodo from the same normalized archive artifacts. Tracking issue: https://github.com/edithatogo/sm-govt-nz/issues/6
  - `ZENODO_DEPOSIT_ENDPOINT` is no longer a blocker: when omitted, the
    `Publish Archives` workflow creates a draft deposition through the default
    Zenodo depositions API and uploads the corpus artifacts to its bucket.
  - Manual publish run `27502440387` created draft deposition `20690547` at
    https://zenodo.org/deposit/20690547 and uploaded the corpus files.
  - Published as v1 on 15 June 2026 with DOI `10.5281/zenodo.20690547`.
    Verified public at https://zenodo.org/records/20690547.
- [x] Task: Publish raw-source bundles separately or as a gated/manual artifact if size or platform terms require it.
- [x] Task: Add dataset manifests with checksums, source coverage, date ranges, and known gaps.
- [x] Task: Add a scheduled/manual GitHub Actions workflow that bundles archive artifacts and publishes to Hugging Face/Zenodo when secrets are configured. Manual runs default to artifact-only and require `publish=true` to send artifacts to external repositories. Artifact-only run `27499923744` passed and uploaded `courts-nz-archive-corpus`.
  - Follow-up cadence decision moved to
    `courts_nz_archive_publication_cadence_20260617` so continuous Hugging Face
    updates and episodic Zenodo snapshots are explicitly reviewed.
  - Cadence decision: weekly scheduled `Publish Archives` updates the Hugging
    Face rolling dataset only; Zenodo snapshots remain manual release-review
    events behind `publish-zenodo-doi`.

## Phase 7: Operational Optimizations
- [x] Task: Add source-health dashboard output to Pages.
- [x] Task: Add no-op scheduled-run monitoring to confirm no duplicate posts are generated.
- [x] Task: Add monthly compaction so Git commits stay small while Hugging Face receives dataset-friendly shards.
- [x] Task: Add Buffer API key rotation reminder before the current key expiry on 12 July 2026.
- [x] Task: Add failure isolation so one blocked source does not stop other archive sources or live Bluesky-to-X mirroring.
- [x] Task: Commit after each completed implementation task and run a review after each phase before starting the next phase.

## Deferred Tracks: Additional Syndication Accounts
- [x] Task: Create one separate conductor track per future outbound platform account after the archive pipeline is stable.
- [x] Task: Require each future syndication track to define posting contracts, source-to-target mapping, duplicate prevention, secret requirements, rate limits, rollback steps, and review gates before implementation.

## Lifecycle Closure
- [x] Task: Review and archive the completed multi-source track lifecycle.
  - `scripts/check_multisource_blockers.py` reports `complete: true`, including LinkedIn seed capture with 2 normalized/report records.
  - Future platform account governance is archived through the platform-specific Conductor tracks and the lifecycle manifest.
