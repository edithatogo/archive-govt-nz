# Treasury resource preflight

The authorized read-only preflight probed all 91 planned resources using HTTPS
`HEAD` requests only. No response bodies were transferred.

- 17 resources had HTTPS observations.
- 12 returned `200` and are candidates for bounded type validation/capture.
- 5 returned `403` and remain unavailable.
- 74 source URLs were non-HTTPS and remain policy-restricted.

The preflight is not a capture or publication result.
