# Specification - NZ Government Social Media Registry & Archiver (Multi-Source Index)

## Overview
This track establishes a central registry, stealth archiver, and decentralized syndication pipeline for New Zealand central and local government social media sites. 

To manage risk and scale, we prioritize implementing the syndication/mirroring engine on a small seed group of agencies *before* expanding the directory to all 600+ public organizations. The system features multi-host git mirroring, academic/decentralized storage redundancy, and parallel agent swarm execution gates.

---

## Phased Roadmap

### Phase 1: Registry Schema, Twitter/X Deactivation Archive, & Multi-Host Git Sync (Current Scope)
*   **Registry Schema Design:** Define the JSON schema for `registry/government_directory.json` supporting hierarchy, timelines, RSS feeds, and newsletters.
*   **Registry Seed:** Seed the registry with initial deactivated/withdrawn Twitter/X accounts.
*   **Compilation & SQLite Export:** Implement `scripts/compile_registry.py` to generate SQLite database and domain JSON files.
*   **Multi-Remote Sync Setup:** Configure automated Git workflows to push commits to GitHub, GitLab, and Codeberg.
*   **Historical Twitter/X Ingestion:** Ingest and commit historical Twitter/X post archives for deactivated target agencies.

### Phase 2: Syndication & Mirroring Engine (Current Scope)
*   **Unified Mirror Engine:** Set up a unified transparency mirror feed targeting open networks (e.g., Bluesky/Threads) for the seed agencies, following the Courts of NZ pattern.
*   **Gating & Opt-Outs:** Implement explicit config flags allowing granular opt-outs per site.

### Phase 3: Directory Expansion (Future Track)
*   **Complete Mapping:** Map all public agencies, departments, and functions (military, police, intelligence, universities, hospitals), identifying those with no social media.
*   **Alternative Feeds:** Map RSS/Atom feeds and email newsletters for all expanded organizations.

### Phase 4: Political Parties, MPs, and Public Sector Leadership Registry (Future Track)
*   **Political Parties:** Identify and map all registered New Zealand political parties, their official social media accounts, websites, and leadership.
*   **Members of Parliament:** Map all current and historically significant MPs, their official parliamentary accounts, electorate office accounts, and personal/public-facing social media.
*   **Public Sector Leaders:** Map official accounts for all public sector leaders — commissioners (e.g., Children's Commissioner, Privacy Commissioner, Health & Disability Commissioner), chief executives of all departments and crown entities, Governors-General, Speakers, Ombudsmen, Auditor-General, and other statutory officers.
*   **Start/End Dates:** For each account, record when the account was established, when the individual held the role, and when the account was last active or deactivated.
*   **Syndication Classification:** For each account, classify whether content is syndicated (cross-posted from another platform) or unique/original to that platform.
*   **Role Tenure Tracking:** Link accounts to specific role tenures so that when leadership changes, the registry reflects which accounts belong to which officeholder and time period.
*   **Schema Extension:** Extend the registry schema to support person records, role records, political party records, and tenure-linked social profiles.

### Phase 5: Crawling, Stealth & Academic/Decentralized Archiving (Future Track)
*   **Swarm Crawler:** Deploy parallelised crawling using the `antigravity-swarm` dispatcher to check health daily.
*   **Wayback Machine Double-Anchor:** Automatically submit every source URL to the Wayback Machine save API.
*   **Censorship-Resistant Archiving:** Automate daily syncs to Hugging Face, your OSF account, and monthly Zenodo DOI releases.

---

## Functional Requirements (Phase 1 & 2)
1.  **Registry Database:**
    *   `registry/government_directory.json` is the source of truth, compiled via script into domain JSONs and `registry/government_directory.db`.
2.  **Historical Archive:**
    *   Retrieve and commit historical posts for deactivated NZ government Twitter/X accounts.
3.  **Multi-Remote Git Mirror:**
    *   Push master updates to GitLab/Codeberg on every commit.
4.  **Syndication Mirror:**
    *   Implement posting adapter to syndicate updates to the unified feed with individual opt-out logic.

## Acceptance Criteria
- `registry/government_directory.json` exists, follows the schema, and is compiled to SQLite database.
- Historical Twitter/X posts for the initial target agencies are archived.
- GitHub Action successfully mirrors the repository to a secondary Git remote.
- The syndication engine runs successfully on the seed group with opt-out controls.
