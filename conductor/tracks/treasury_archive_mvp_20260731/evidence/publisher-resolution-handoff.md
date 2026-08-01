# Publisher-resolution handoff

Status: **draft-not-sent**

This handoff describes how to submit and record the prepared Treasury/data.govt.nz
source-resolution packet. It does not select a recipient, send a message, or grant
permission to use credentials. The JSON and Markdown request packet remains the
authoritative draft until a sender and recipient are explicitly approved.

## Recipient decision

Recommended recipient: the official data.govt.nz catalogue owner or Treasury open-data
contact responsible for the `the-treasury` organisation. Confirm the current contact
through an official government page immediately before sending. Do not infer a personal
address from metadata, and do not send to a third-party mirror or an unverified address.

Fallback: if the catalogue owner cannot be confirmed, retain the packet as
`draft-not-sent` and continue scheduled probes. Do not substitute a general contact
without recording the basis for that choice.

## Safe submission rules

- Send the generated packet without resource payloads, credentials, signed URLs, or
  personal information.
- Preserve the packet checksum and request timestamp before sending.
- Request one disposition per resource: an authoritative HTTPS replacement, withdrawal
  or successor, approved access procedure, or no change.
- Do not request or accept an HTTP-only exception or an undocumented mirror.
- Treat any supplied URL as a candidate only; validate HTTPS, identity, rights, and
  content independently before capture.

## Response recording

Record a response as a separate, immutable JSON receipt validated against
`schemas/archive/publisher-resolution-response-v1.schema.json`. The response must
include the request receipt, sender organisation/role, received timestamp, and one
disposition per resource where possible.

Use these dispositions:

- `replacement`: requires an HTTPS URL and evidence receipt; validate before promotion.
- `withdrawn`: preserve the original metadata and create/retain a tombstone.
- `restricted`: retain the restricted state and approved access note; do not bypass it.
- `no-change`: retain the current state and re-probe on schedule.
- `unknown`: record the response but take no state-changing action.

Keep the original message or attachment outside the public archive if it contains
personal information or credentials. Store only a redacted evidence receipt and a
cryptographic digest/reference to the source message.

## Promotion gate

An accepted replacement must pass the existing secure-source and rights policy, match
the CKAN resource identity (or have an explicit successor mapping), and produce a new
capture/version receipt. A response alone never marks a payload captured. Unresolved
resources remain tombstones and continue bounded re-probing.
