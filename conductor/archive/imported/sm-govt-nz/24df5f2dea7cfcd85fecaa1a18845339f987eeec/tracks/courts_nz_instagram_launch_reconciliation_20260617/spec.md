# Specification - Courts of New Zealand Instagram Launch Reconciliation

The earlier Instagram track records launch-complete evidence, but the current
runtime config keeps Instagram disabled and excludes it from the Courts of New
Zealand `syndicate_to` list. This track reconciles that mismatch before any
claim that Instagram is live.

## Requirements

1. Treat `config.json` and committed delivery state as the launch source of
   truth.
2. Do not post under a personal Instagram identity.
3. Use official Meta Instagram APIs only.
4. Keep Instagram delivery state separate from Bluesky, Threads, Facebook, and
   X.
5. Keep historical replay disabled unless a separate review approves current-feed
   archival posting.

## Done

- The reason for the current disabled runtime state is documented.
- The Instagram credential probe passes against the intended mirror account.
- A dry-run payload is reviewed.
- Instagram is either:
  - enabled with one controlled live post and verified public URL; or
  - explicitly deferred with the blocker recorded.
- The older Instagram track is updated to point to this reconciliation outcome.
