# Implementation Plan

## Phase 1: Credential hygiene and read-only contract

- [x] Task: Remove normal Facebook and LinkedIn passwords from repository secrets and document rotation.
    - [x] Add validation rejecting password-shaped configuration for archival workflows.
    - [x] Confirm no workflow references password secrets.
- [x] Task: Add tests asserting capture-only behavior and disabled write/mirror scopes.
- [ ] Task: Conductor - User Manual Verification 'Credential hygiene and read-only contract' (Protocol in workflow.md)

## Phase 2: Bluesky completion

- [x] Task: Validate the dedicated Bluesky app-password configuration.
    - [x] Run the scheduled archive workflow with the registered source manifest.
    - [x] Confirm records, diagnostics, and publication state.
- [x] Task: Fix any manifest, adapter, or workflow faults and rerun the bounded proof.
- [ ] Task: Conductor - User Manual Verification 'Bluesky completion' (Protocol in workflow.md)

## Phase 3: Facebook Page access

- [x] Task: Detect and report whether `edithatogo@gmail.com` manages any registered government Pages.
- [ ] Task: Add the Page ID and read-only Page Access Token only after authorised Page administration exists.
    - [ ] Keep `FACEBOOK_GRAPH_CAPTURE_ENABLED` false until validation passes.
    - [ ] Run a dry-run and one-Page capture proof before expanding.
- [ ] Task: Classify missing Page ownership, reCAPTCHA, or token approval as external-access evidence.
- [ ] Task: Conductor - User Manual Verification 'Facebook Page access' (Protocol in workflow.md)

## Phase 4: LinkedIn developer access

- [x] Task: Inspect the logged-in developer console without creating an app or Page without an authorised association.
- [ ] Task: If an authorised LinkedIn Page exists, configure a zero-cost app with privacy URL, logo, and read-only product approval.
    - [ ] Store only the approved read token as `LINKEDIN_ACCESS_TOKEN`.
    - [ ] Run a dry-run and one-organisation capture proof.
- [x] Task: Otherwise document the authorised export intake path and retain `terminal_external_access` status.
- [ ] Task: Conductor - User Manual Verification 'LinkedIn developer access' (Protocol in workflow.md)

## Phase 5: Coverage, publication, and closeout

- [ ] Task: Rebuild source reports and completion matrix with evidence links and blocker classes.
- [ ] Task: Confirm monthly Hugging Face and Zenodo guards remain unchanged and no same-month duplicate publication occurs.
- [ ] Task: Run targeted tests, YAML parsing, and opt-in remote proofs.
- [ ] Task: Review findings, apply fixes, update this plan, and archive the track when acceptance criteria are met.
- [ ] Task: Conductor - User Manual Verification 'Coverage, publication, and closeout' (Protocol in workflow.md)
