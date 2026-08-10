# Issue #14 execution receipt

## Repository hardening context

- Added `AGENTS.md` with explicit solo-maintainer and operational constraints.
- Added repository issue and pull-request templates under `.github/`.
- Added one-command validation harness scripts at:
  - `scripts/validate.sh`
  - `scripts/validate.ps1`

## Verification command run

```powershell
./scripts/validate.ps1
```

- Note: merge and branch-protection settings (rulesets, bot inventory, and recovery
  guardrails) remain to be confirmed directly in GitHub repository settings.
