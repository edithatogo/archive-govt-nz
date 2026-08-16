# Specification - Post Archiver, Edit Tracker & Zenodo/Hugging Face Publisher

## Overview
This specification defines how the system records full post details (including images and alt-text) locally, tracks edits to existing posts, publishes these datasets to Hugging Face and Zenodo for research access, and handles historical backfills without causing feed spam.

## Requirements
1.  **Edit Ingestion & Tracking:**
    *   Compare newly fetched post contents against local archive files.
    *   If a modification is found, log it under an `edit_history` list with timestamps within the post's JSON file (`/historical_archive/<agency>/<post_id>.json`).
2.  **Zenodo & Hugging Face Publishing:**
    *   Write a script to bundle local JSON files, gzip them, and push them to Zenodo (requesting a DOI) and Hugging Face Datasets via their respective upload APIs.
3.  **Historical Backfill Management:**
    *   Support importing past posts from RSS feeds or profile scrollings.
    *   Provide option to post them *unlisted* on Mastodon, or present them solely on the web dashboard to prevent flooding live feeds.
