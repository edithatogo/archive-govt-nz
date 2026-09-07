# P2.14 probe robots runtime compatibility

## Confirmed compatibility boundary

The package permits Python >=3.14. The upstream
[CPython v3.14.0 parser](https://raw.githubusercontent.com/python/cpython/v3.14.0/Lib/urllib/robotparser.py)
uses prefix matching in `RuleLine.applies_to`, whereas the
[v3.14.6 parser](https://raw.githubusercontent.com/python/cpython/v3.14.6/Lib/urllib/robotparser.py)
contains newer pattern-handling logic. Behavior observed on 3.14.6 is not proof
that the entire allowed runtime range interprets wildcard/end-anchor rules.
This independently confirms the compatibility risk raised during PR417 review.
No source-site requests were made to investigate this; only upstream source was
read. No remote writes or full-cohort replay occurred.

## Conservative probe guard

`robots_path_rules_supported` inspects every Allow/Disallow path before
`RobotFileParser` is constructed or consulted for page admission. A literal or
percent-decoded `*` or `$` rejects the entire robots file for this bounded probe,
including patterns for unrelated paths or other user-agent groups. Comments,
the standard `User-agent: *` selector and sitemap values are not path rules.
This intentionally sacrifices availability instead of depending on version-
specific pattern or group interpretation. It is not a full robots implementation
or RFC-conformance guarantee for the supported runtime range.

The result is `robots_unsupported_rules`, `allowed: null`, no page request and no
page success. The dated robots transport/digest remains evidence; an unsupported
rule is not reclassified as public access or a source owner's prohibition.
Plain prefix rules continue through the existing parser and corrected per-hop
crawl-delay logic. This guard also protects `observe_links`, which reuses the
same collector. Parent separately owns the analogous candidate-assessment guard;
this commit does not edit that module or its tests.

## Tests and review

Seven new complex-rule regressions failed on the previous implementation, then
passed after the guard. They mock `can_fetch` as permissive legacy behavior and
assert it is never called and only robots is requested. Five simple-rule/comment
cases and a different-agent complex-rule case verify conservative boundaries.
Encoded stars/dollar markers, case/whitespace, Allow and Disallow paths are covered.
The test does not assume the host parser provides modern wildcard behavior.

Focused suite: 249 tests pass; Ruff, format and scoped BasedPyright pass. New guard
paths are exercised; whole probe module coverage remains below 100% and no full
harness is claimed. Parent owns combined full validation. Historical observations,
the P2.13 correction and linked pre-fix provenance remain byte-identical; neither
this fix nor offline validation certifies their historical robots compliance.

Conductor review found no unresolved in-scope guard issue. Python/general guides
apply; no dependency or minimum-version bump, global registry edit, policy
exception, rights decision, schedule or publication change. Integrate after the
linked-cohort commit, retaining parent's accepted P2.5–P2.8 statuses and rechaining
only new evidence appends against the parent's ledger.
