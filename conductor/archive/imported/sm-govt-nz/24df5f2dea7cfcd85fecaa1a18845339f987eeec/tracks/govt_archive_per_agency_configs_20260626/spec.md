# Spec - NZ Government Archive - per-agency source inventory and RSS feed configuration

## Problem
Individual agency source manifests, readiness data, and RSS live data exist across multiple JSON files in the conductor directory. There is no single authoritative per-agency config file that an automated capture workflow can consume directly.

## Scope
Generate per-agency source inventory JSON files that consolidate:
- All discovered source types (Bluesky accounts, RSS feeds, website pages) per agency
- RSS feed configuration files with feed URLs, metadata, and health status
- A consistent directory structure under `config/agencies/`

## Required Outputs
- Run `scripts/generate_agency_configs.py` to produce config files
- Validate all config files using `scripts/validate_agency_configs.py`
- Confirm 16 agency configs are generated and validated
- Create per-agency config index file for quick lookup

## Acceptance Criteria
- All agencies with discovered sources have valid, validated config files in `config/`
- Configs are consistent with registry agency IDs and readiness matrix source records
- Agency workflow patterns are documented for downstream scheduled capture
- Validation script passes with zero errors
