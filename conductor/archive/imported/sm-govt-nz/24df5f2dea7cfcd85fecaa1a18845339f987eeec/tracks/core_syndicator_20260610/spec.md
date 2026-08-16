# Specification - Core Syndicator and Transparency Website

## Overview
This specification details the MVP implementation for the NZ Government Bluesky Syndication engine and its accompanying open-government transparency website.

## Functional Requirements
1.  **Bluesky Ingestion:**
    *   Connect to the AT Protocol (Bluesky) API.
    *   Fetch new posts from a whitelist of target NZ government accounts.
    *   Track the last processed post ID per account using `conductor/state.json`.
2.  **Syndication Adapters:**
    *   **X (Twitter):** Authenticate via OAuth 1.0a (API v2) and post text (up to 280 characters) or threads.
    *   **Threads:** Post text and media via Threads Graph API.
    *   **Mastodon:** Mirror post text to a specified Mastodon server/account.
    *   **Discord:** Deliver posts to a Discord channel via Webhooks.
    *   **LinkedIn:** Publish post updates to a LinkedIn page/profile.
3.  **Content Formatting & Truncation:**
    *   Parse Bluesky's 300-char posts to fit other platforms (like X's 280-char limit) by appending links to the original posts or creating post threads.
    *   Carry over image attachments and alt text for accessibility.
4.  **GitHub Pages Site:**
    *   Serve a single-page static HTML dashboard.
    *   Provide open-government rationale and disclaimer.
    *   List currently monitored agencies.

## Technical Design & Architecture
*   **Language:** Python 3.11+
*   **Libraries:** `atproto`, `requests`, `requests-oauthlib`
*   **Data Store:** Git-backed `conductor/state.json` file.
*   **CI/CD:**
    *   `ci.yml`: Run `ruff` lint/format and run unit tests (pytest).
    *   `syndicate.yml`: Running on a 15-minute cron schedule.
    *   `pages.yml`: Deploys the web UI to GitHub Pages on merges to main.
