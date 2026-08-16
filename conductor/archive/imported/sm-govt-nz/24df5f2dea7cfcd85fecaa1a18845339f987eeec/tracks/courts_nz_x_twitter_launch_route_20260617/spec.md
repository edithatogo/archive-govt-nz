# Specification - Courts of New Zealand X/Twitter Launch Route

Complete the X/Twitter outbound lane for the Courts of New Zealand mirror. The
current runtime config keeps `x.enabled` false, so this track is not complete
until a reviewed posting route is selected, validated, enabled, and proven with
delivery state.

## Requirements

1. Post only as the dedicated mirror identity, not as a personal account.
2. Prefer a supported API or approved scheduler route over browser automation.
3. Keep historical archive replay separate from new-forward syndication.
4. Preserve duplicate-prevention state per target.
5. Record token expiry, rotation reminder, and cost/free-tier assumptions before
   enabling scheduled posting.
6. Require one controlled live post and public URL verification before launch
   status can be marked complete.

## Accepted Routes

- Direct X API, only if posting entitlement and costs are confirmed.
- Buffer or equivalent scheduler, only if the plan, token expiry, queue behavior,
  and API limits are documented.
- Browser automation is out of scope unless a later explicit review approves it
  and adds platform-risk guardrails.

## Done

- `config.json` includes `x` in the Courts of New Zealand `syndicate_to` list.
- `syndication_targets.x.enabled` is true only after the selected route passes
  validation.
- A dry-run payload is reviewed.
- A controlled live post succeeds.
- The public X URL and delivery state are committed.
- The route has a documented free-tier/cost position and rotation reminder.
