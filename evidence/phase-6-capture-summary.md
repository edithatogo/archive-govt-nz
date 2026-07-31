# Treasury capture summary

The bounded capture run transferred payloads for the 12 resources that returned
HTTP 200 during the authorized read-only preflight. All 12 were captured into
the local content-addressed object store; no resource failed and no publication
was attempted.

- Run receipt: `build/live/capture-20260731.json`
- Preflight receipt: `build/live/preflight-20260731T173027.json`
- Object store: `build/objects`
- Limits: 512 MiB per resource, 10 GiB total, concurrency 4

The remaining five HTTPS resources (HTTP 403) and 74 non-HTTPS resources remain
unavailable or restricted and are not silently treated as captured.
