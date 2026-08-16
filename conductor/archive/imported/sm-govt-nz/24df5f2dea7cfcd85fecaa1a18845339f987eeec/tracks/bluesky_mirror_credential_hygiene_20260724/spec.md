# Specification

Require Bluesky app passwords for automation and isolate them in per-account GitHub Environments. Detect and reject primary-password usage in automation paths. Remove persistent local primary-password environment variables, document rotation, and provide credential-health checks that never expose secret values.

Credential rotation and remote secret replacement remain explicit operator actions.
