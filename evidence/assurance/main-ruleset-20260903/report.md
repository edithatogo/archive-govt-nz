# Main integrated-assurance ruleset readback

This evidence supersedes only the hosted-enforcement finding recorded for Prompt
20 in issue [#354](https://github.com/edithatogo/archive-govt-nz/issues/354).
The original 2026-09-02 evidence remains unchanged.

At `2026-09-03T09:39:08Z`, GitHub returned active repository ruleset
`22180861`, `main-integrated-assurance`, for `~DEFAULT_BRANCH`. The direct
ruleset response and the repository ruleset listing both identify the same
active rule. The readback is bound to target `main` commit
`b408aa3660b5de9d68fec31ef2273938226e5f18`.

The ruleset prevents branch deletion and non-fast-forward updates, requires a
pull request with all review threads resolved, and strictly requires these
contexts against the latest target branch state:

- `Assurance (ubuntu-latest)`
- `Assurance (macos-latest)`
- `Assurance (windows-latest)`
- `analyze`
- `lint`
- `codecov/patch`

The pull-request rule requires zero approving reviews. It does not require code
owner review, approval of the last push, or extra approval for unattributed
changes. This is the intended solo-maintainer posture: no second person is
required.

`RepositoryRole` actor `5` has `always` bypass mode, and the authenticated
maintainer readback reports `current_user_can_bypass: always`. This is the
approved emergency path. Its use remains a hosted, attributable ruleset bypass;
the ordinary path is the pull request and strict required-check gate.

The readback proves the hosted policy configuration. It does not claim that all
six contexts ran successfully on the receipt's target commit. Exact-head hosted
run results remain separate assurance evidence.

Files:

- `ruleset-22180861-readback.json`: deterministic direct-response projection;
- `repository-rulesets-readback.json`: deterministic repository-list projection;
- `main-ruleset-readback-receipt.json`: normalized assertions, hashes, target
  commit, authorization scope, and bounded interpretation.

The projections omit only GitHub's opaque `node_id` and redundant `_links`
fields. The receipt retains SHA-256 hashes of both source responses and the
projected files, so the evidence remains fixity-bound without storing
scanner-sensitive opaque identifiers.
