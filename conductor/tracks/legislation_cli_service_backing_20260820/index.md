# Fail-closed service-backed legislation CLI correction

Correct the merged PR #151 legislation CLI on top of the service and global
CLI corrections. Preserve useful command names and compatibility mappings,
but remove duplicated transport, fabricated defaults, unauthenticated state,
and token-only publication verification.

This track is local and sequence-gated. It must not produce a second open PR
while the service correction remains unmerged.
