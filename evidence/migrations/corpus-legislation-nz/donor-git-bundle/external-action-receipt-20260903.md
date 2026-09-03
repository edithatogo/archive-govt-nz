# Prompt 19 external-action receipt addendum

Observed at `2026-09-03T09:16:30Z` from the GitHub API. This dated addendum
supersedes only the external-action and publication-status fields in the earlier
verification receipt. The earlier bundle verification and failed-attempt
evidence remain unchanged.

The first direct push of the donor redirect failed because donor branch
protection required the `tests` status check. GitHub does not publish rejected
pushes as durable API objects, so that failure is explicitly attributed to the
operator command receipt, which retained GitHub's `GH006` protected-branch
error and the message `Required status check "tests" is expected.` The
unarchive and emergency-rearchive response files have mtimes
`2026-09-03T19:09:27+10:00` and `2026-09-03T19:09:32+10:00`; final API readback
reports the donor archived. The successful path used donor PR
[`#185`](https://github.com/edithatogo/corpus-legislation-nz/pull/185), which
merged as `905f9e07c17af9d9d25dbe2b1c052fb8a290a4e3` at
`2026-09-03T09:13:44Z` after all 16 hosted checks passed. That merge is now
donor `main`; the tag below deliberately retains the earlier operational
state. The remotely read README
exactly matches the reviewed candidate at SHA-256
`692c703b360fc404f314826fcea2b3c014710e9d1721320a5c346f6dcae0f6f0`.

The donor remains archived. Annotated tag `migration-final-20260821` resolves
first to tag object `cdd6a397a96773c06519e2e86bbe7a606b26bd58`, then to the
frozen operational commit `b40587f1b1aec7356a0f623916fcc8212397d283`. Its
remote message matches the reviewed message bytes at SHA-256
`0e707b9af12fca40ef685670125eab620d35c206736d39910205b95e1d76e48e`.
The tag is annotated but unsigned; no signature claim is made.

The target release
[`corpus-legislation-nz-final-archive-20260903`](https://github.com/edithatogo/archive-govt-nz/releases/tag/corpus-legislation-nz-final-archive-20260903)
is public, non-draft, and non-prerelease, published at
`2026-09-03T09:14:15Z`. Its sole bundle asset is 2,365,303 bytes and GitHub
reports digest
`f125f91b06264a97e59f65fac47878a74d646c915f12c0b05841c1550ec741c2`,
matching the previously verified bundle. This proves public GitHub readback; it
does not assert independent non-GitHub durability. An unauthenticated download
at `2026-09-03T09:24:01Z` independently returned the same 2,365,303 bytes and
SHA-256.
