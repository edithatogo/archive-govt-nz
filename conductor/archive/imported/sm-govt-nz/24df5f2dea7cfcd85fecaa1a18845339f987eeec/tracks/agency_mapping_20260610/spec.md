# Specification - NZ Agency Social Registry & Self-Improving Agent Framework

## Overview
This track defines the data structures and automated workflows to map all public agencies in New Zealand and their social media footprints, run a cross-platform gap analysis, and provide a framework for the repository to build and refine its own agent capabilities.

## Functional Requirements
1.  **NZ Government Agency Directory:**
    *   Maintain a structured JSON directory of all NZ government ministries, departments, and crown entities.
    *   Include metadata: agency type, portfolio, URL, and status.
2.  **Social Media Profile Mapping:**
    *   Map each agency's profiles across current and historical platforms: Bluesky, X, Threads, Mastodon, Facebook, Instagram, YouTube, TikTok, LinkedIn, and RSS feeds.
    *   Track historical deactivation dates (e.g., when an agency left X).
3.  **Cross-Platform Gap Analysis:**
    *   Compute and display gaps: which agencies are publishing on proprietary networks but missing on open/decentralized networks.
    *   Present the gap analysis visually on our public website dashboard.
4.  **Episodic Updater Workflow:**
    *   Create a scheduled GitHub Actions workflow to periodically scan, verify profile health (e.g. check for deactivations or new profiles), and commit updates back to the registry.
5.  **Self-Improving Agent Framework (SOTA & Bleeding Edge):**
    *   Define a modular folder structure (`/agents`, `/skills`, `/rules`) inside the repository.
    *   Build standard rules for how agents can autonomously inspect repository state, run evaluations on their code, write new python-based skills, and deploy updates.
    *   Implement state-of-the-art tools and patterns (e.g., automated execution of code steps, dynamic prompt updates, and feedback loops).

## Technical Architecture
*   **Registry Format:** `registry/agencies.json` storing structured agency data.
*   **Gap Analyzer Script:** `scripts/gap_analyzer.py` compiling metrics and generating a JSON report.
*   **Episodic Workflow:** `.github/workflows/update_registry.yml` running on a weekly/monthly cron schedule.
*   **Agent Assets Folder:** `/agent_framework` with standard definitions for custom skills, workflows, and evaluation criteria.
