# Specification - Mirror Account Follow Sync

## Overview
This track implements bi-directional follow synchronization across active mirror accounts where supported platform APIs make that safe and maintainable. It starts with relationship mapping and read-only evidence, then allows live follow execution only for platforms with confirmed official API support and explicit credentials.

---

## Phased Roadmap

### Phase 1: Relationship Mapping
*   **Target Mapping:** Parse the config files to build a bi-directional follow requirements matrix (who should follow whom).
*   **Follow Verification Probes:** Implement read-only probes where the platform exposes supported public or authenticated visibility without creating side effects.
*   **Manual Review Queue:** Record platforms that cannot be checked through supported APIs as manual-review tasks.

### Phase 2: Follow State Redundancy
*   **State Cache:** Create `conductor/follow_sync_state.json` to persist verified follow states, evidence timestamps, platform identifiers, and manual-review notes.
*   **Credential Boundary:** Do not commit browser sessions, cookies, passwords, local storage exports, or credential-derived artifacts. GitHub Actions may use repository secrets only for supported API calls.

### Phase 3: Supported API Execution
*   **API Write Execution:** Implement programmatic follows only after a platform's official API route, scopes, and rate limits are documented.
*   **Unsupported Platforms:** Keep Threads, Instagram, Facebook, LinkedIn, and any platform without a confirmed follow API as manual tasks until a supported route is added in a separate reviewed track.
*   **Workflow Integration:** Add dry-run reporting first. Live execution must be opt-in and gated separately from the syndication posting path.

### Phase 4: Wider Group Scaling (Future Scope)
*   **Auto-Onboarding Sync:** Auto-sync follows for any newly registered agency mirror accounts when they are added to the directory.

---

## Functional Requirements
1.  **Registry Relationship Matrix:**
    *   Identify all active mirror accounts and map bi-directional follow status.
2.  **Follow Execution Adapter:**
    *   `scripts/sync_mirror_follows.py` executes follows only using supported direct APIs with explicit credentials.
3.  **Manual Review Output:**
    *   Unsupported follow operations are emitted as actionable manual-review records, not browser-control scripts.
4.  **Scheduled Action:**
    *   Integrate read-only follow-sync checks into the daily automated workflow cycle only after the dry-run output is stable.

## Acceptance Criteria
- `scripts/sync_mirror_follows.py` compiles and correctly identifies missing follows.
- Read-only probes accurately check supported platforms and flag unsupported platforms for manual review.
- Programmatic follow execution succeeds for at least one supported API path before any live workflow is enabled.
- Follow state cache is committed to `conductor/follow_sync_state.json`.
- No browser sessions, cookies, password material, or stealth browser automation are added to the repo or GitHub Actions.
