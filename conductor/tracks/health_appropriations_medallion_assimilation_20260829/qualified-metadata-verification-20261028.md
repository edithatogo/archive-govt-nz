# Qualified metadata reconstruction and publisher checksum correction

## Bounded Phase 7 scope

The new read-only verifier reconstructs v1 rights graphs, v2 discovery and v3
partner metadata from exact source, Silver, Gold, rights and partner pins. It
requires a closed metadata inventory and exact manifest/payload bytes. Rehashing
a forged blanket licence or an unsupported positive federation link cannot make
it pass. Schema-as-code records verification separately from release approval.

The five qualified headline editions remain source-separated. Existing installed
metadata, retained publisher snapshots and the historical README mismatch remain
unchanged and reproducible. No blanket redistribution or positive join is added.
Full standards conformance, other product profiles and the Phase 7 checkpoint
remain open.

## Explicitly approved publisher correction

The maintainer approved changing only the README entry in the medicines
catalogue SHA256SUMS. The frozen parent is
`117caee3e1cf31d476c6a66a9860963cc35ed0cb`; approved payload SHA256 is
`b0ca284d64824f14e8ddb4a618917dba87114ddac9ea3cf99c4e9b0d3336e00d`.
README SHA256 must remain
`02825cc9f6dd66acf7346711dede1cde366a0ce5ba5b21462f57ff151c0c1736`.

The separate hosted checksum job does not invoke harvesting or notifications.
It retains a public metadata intent artifact before any write, requires green
protected contexts on its executing revision, qualifies the publisher account
and write-token role, and sends one parent-bound single-path commit. An
uncertain response leads to anonymous verification, never a resend. Readback
compares all 62 file identities and both metadata payloads. Rerun attempts cannot
write. Existing scheduled harvesting retains its original operation.

Native publication and protected delivery evidence will be added after their
actual completion; preparation and test doubles do not establish a hosted write.

## Validation

Focused tests cover reconstruction, forged metadata, unknown members, hosted
approval/check guards, parent-bound single-send behavior, uncertain responses,
and workflow side-effect separation. Native verification reconstructs all three
installed versions without changing sources or metadata. The final harness and
exact-head protected Actions remain required before delivery.

Local assurance passed with 8,619 tests, 14 skips, 96.53% coverage against the
unchanged 80% floor, 86 schemas / 76 fixtures, parity 9/9, all mutation lanes,
hygiene, CAS benchmark, dependency audit, licence inventory, secret scan and
validated 118-component SBOM. A connection outage affected the audit; its
existing bounded read-only attempt completed after connectivity recovered.
The interruption after secret scanning required only the remaining SBOM stage.
Integrated PRs #799 and #800 with nine and fourteen affected tests respectively;
unchanged full-suite evidence is retained and final hosted assurance is required.

Hosted read-only inspection run 40614016612 at `d95352db` passed, retained the
approved correction bytes and skipped the entire harvest/publication job.
This qualifies preparation on the Python 3.15.1 runner, not a publisher write.
