# Run log

- 2026-08-20: Audited the stacked base at `5c7ae9c`. Confirmed stale protocol
  advertisement, permissive initialization, pre-initialization service, invalid
  notification handling, absent cursor validation, incorrect resource errors,
  flat CAS discovery, and affirmative empty-store status.
- 2026-08-20: Added adversarial stable-protocol controls. The red run stopped at
  collection because the implementation did not define the MCP `-32002`
  resource-not-found error, before reaching the remaining expected failures.
