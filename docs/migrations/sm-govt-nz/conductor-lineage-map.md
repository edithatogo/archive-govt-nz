# Conductor Lineage Reconciliation Map

This document records the disposition of all 39 tracks from the donor repository (`edithatogo/sm-govt-nz` at commit `24df5f2dea7cfcd85fecaa1a18845339f987eeec`).

All donor tracks are preserved immutably under:
`conductor/archive/imported/sm-govt-nz/24df5f2dea7cfcd85fecaa1a18845339f987eeec/tracks/`

## Disposition Summary

- **Total Donor Tracks**: 39
- **Historical Imports (Completed)**: 10
- **Mapped to Target Consolidation Tracks**: 21
- **Superseded by Target Native Capabilities**: 5
- **Deferred (API Policy / Evaluation Gate)**: 3

## Detailed Lineage Table

| Donor Track ID | Disposition | Target Consolidation Track | Rationale |
| :--- | :--- | :--- | :--- |
| `agency_mapping_20260610` | `mapped_to_target_track` | `canonical_archive_contracts_20260817` | Transplanted into unified core registry in Track 4. |
| `archiver_zenodo_20260610` | `mapped_to_target_track` | `publication_and_distribution_alignment_20260817` | Preserves Zenodo Concept DOI 20991132 in Track 7. |
| `bluesky_government_mirror_programme_20260721` | `mapped_to_target_track` | `source_adapter_migration_programme_20260817` | Migrated to async Bluesky capture adapter in Track 5. |
| `bluesky_historical_backfill_rollout_20260721` | `mapped_to_target_track` | `preservation_replay_recovery_assimilation_20260817` | CAS backfill and replay in Track 6. |
| `bluesky_mirror_credential_hygiene_20260724` | `historical_import` | None | Historical credential hygiene policy imported immutably. |
| `bluesky_mirror_safety_observability_20260721` | `mapped_to_target_track` | `cli_mcp_operator_interface_convergence_20260817` | Unified with webhook alerting in Track 8. |
| `core_syndicator_20260610` | `superseded` | `canonical_archive_contracts_20260817` | Superseded by streaming CAS and W3C PROV-O ledger in Track 4. |
| `courts_nz_archive_publication_cadence_20260617` | `historical_import` | None | Historical cadence baseline imported immutably. |
| `courts_nz_bluesky_archive_replay_20260613` | `mapped_to_target_track` | `preservation_replay_recovery_assimilation_20260817` | Replay harness unified in Track 6. |
| `courts_nz_bluesky_launch_ops_20260613` | `historical_import` | None | Completed pilot ops. |
| `courts_nz_bluesky_mirror_20260612` | `historical_import` | None | Completed pilot mirror. |
| `courts_nz_bluesky_profile_archive_20260613` | `mapped_to_target_track` | `source_adapter_migration_programme_20260817` | AT Protocol profile archiving in Track 5. |
| `courts_nz_facebook_meta_api_20260613` | `deferred` | None | Deferred pending Graph API public access token resolution. |
| `courts_nz_instagram_launch_reconciliation_20260617` | `historical_import` | None | Completed pilot reconciliation. |
| `courts_nz_instagram_meta_api_20260613` | `deferred` | None | Deferred pending API policy clearance. |
| `courts_nz_mirror_20260611` | `historical_import` | None | Completed initial mirror. |
| `courts_nz_multisource_archive_20260612` | `mapped_to_target_track` | `source_adapter_migration_programme_20260817` | Multi-source orchestrator consolidated in Track 5. |
| `courts_nz_threads_adapter_launch_20260613` | `mapped_to_target_track` | `source_adapter_migration_programme_20260817` | Threads adapter consolidated in Track 5. |
| `courts_nz_threads_api_credentials_20260613` | `historical_import` | None | Completed credentials configuration. |
| `courts_nz_threads_historical_replay_policy_20260613` | `mapped_to_target_track` | `preservation_replay_recovery_assimilation_20260817` | Replay policy consolidated in Track 6. |
| `courts_nz_threads_mirror_20260612` | `historical_import` | None | Completed mirror run. |
| `courts_nz_x_twitter_launch_route_20260617` | `mapped_to_target_track` | `source_adapter_migration_programme_20260817` | X public feed scraper in Track 5. |
| `github_integrations_20260610` | `superseded` | `release_cutover_publication_continuity_20260817` | Superseded by canonical target workflows in Track 12. |
| `govt_archive_bluesky_onboarding_20260626` | `mapped_to_target_track` | `source_adapter_migration_programme_20260817` | Onboarded accounts merged into registry in Track 4 and 5. |
| `govt_archive_external_publication_20260625` | `mapped_to_target_track` | `publication_and_distribution_alignment_20260817` | Publication pipelines unified in Track 7. |
| `govt_archive_per_agency_configs_20260626` | `mapped_to_target_track` | `canonical_archive_contracts_20260817` | Per-agency seed configs unified in Track 4. |
| `govt_archive_provenance_fixity_20260625` | `superseded` | `preservation_replay_recovery_assimilation_20260817` | Superseded by cryptographic CAS fixity and PROV-O in Track 6. |
| `govt_archive_quality_observability_20260625` | `mapped_to_target_track` | `cli_mcp_operator_interface_convergence_20260817` | Quality observability unified in Track 8. |
| `govt_archive_readiness_matrix_20260625` | `historical_import` | None | Historical readiness evidence imported immutably. |
| `govt_archive_rss_onboarding_20260626` | `mapped_to_target_track` | `source_adapter_migration_programme_20260817` | RSS onboarding unified in Track 5. |
| `govt_archive_scheduled_multisource_20260626` | `mapped_to_target_track` | `release_cutover_publication_continuity_20260817` | Scheduled workflows unified in Track 12. |
| `govt_credentialed_readonly_access_resolution_20260717` | `historical_import` | None | Read-only access resolution imported immutably. |
| `govt_discovery_self_learning_20260625` | `deferred` | None | Self-learning discovery deferred pending bounded evaluation. |
| `govt_registry_20260614` | `mapped_to_target_track` | `canonical_archive_contracts_20260817` | Core registry imported in Track 4. |
| `govt_registry_account_classification_20260622` | `mapped_to_target_track` | `canonical_archive_contracts_20260817` | Classification taxonomy imported in Track 4. |
| `govt_registry_mp_expansion_20260621` | `mapped_to_target_track` | `canonical_archive_contracts_20260817` | MP account seeds imported in Track 4. |
| `govt_registry_quality_gates_20260622` | `superseded` | `capability_assimilation_architectural_refactor_20260817` | Superseded by 18 target assurance gates in Track 11. |
| `govt_registry_refresh_cadence_20260622` | `historical_import` | None | Historical cadence imported immutably. |
| `sync_mirror_follows_20260614` | `superseded` | `canonical_archive_contracts_20260817` | Superseded by explicit declarative registry seed lists. |
