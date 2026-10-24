# Scheduled discovery report — 2026-10-24

The scheduled Health discovery workflow now writes a deterministic Markdown
report beside its JSON heartbeat and preserves both in the existing always-run
artifact upload. The report contains only bounded workflow/discovery states,
the discovery manifest SHA-256, dataset count, and reason-coded drift counts.
It never copies dataset titles, notes, locators, raw responses, credentials,
signed URLs, or payload bytes. The machine receipt and report both state that
capture, Silver normalization, validation, and publication were not run.

The heartbeat renderer allowlists each reported field and substitutes safe
unknown/not-available values for malformed inputs. JSON and Markdown use
separate atomic temporary files; the CLI rejects input/output and output/output
path collisions. The workflow retains its existing `contents: read` permission,
concurrency group, and metadata-only discovery behavior. This change adds no
payload capture, remote write, credential, or publication step.

Focused validation: scheduled heartbeat and workflow-policy suites pass 25
tests on Python 3.15.1. Full repository validation and hosted checks are tracked
in the delivery PR; the wider Phase 8 scheduling/recovery gates remain open.
