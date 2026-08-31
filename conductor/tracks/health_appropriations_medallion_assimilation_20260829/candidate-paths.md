# Portable candidate original paths

The candidate builder now validates every original destination before creating
the output directory, accessing CAS or copying any object. Identifiers are
bounded ASCII components; reserved Windows devices, traversal, unsafe suffixes
and case-insensitive destination collisions fail closed. Existing originals,
candidate v4 and Hugging Face bytes are unchanged.

This is a destination-name guard only. It does not establish URL eligibility,
rights applicability, derivative-to-source joins or publication readiness. The
broader additive candidate planner remains separate work.

## Evidence

- Functional checkpoint: `1a3356a`; source SHA-256
  `c1cd3164ef922167875469d1faa575d7aedbf54c6ac8188366f28db929f8200d`.
- Initial red contract failed because the new module did not exist. A later
  test-loader import mistake was corrected to the repository's explicit module
  loading pattern. Neither failure establishes an existing production defect.
- 37 focused cases pass, including valid-first/invalid-second and collision
  integration cases with forbidden CAS/copy spies, boundary and property tests.
  Critical coverage is 100% across 26 statements and eight branches.
- Cold, unfiltered one-worker mutation: five of five killed, zero survivors,
  timeouts, errors, pardons or cache hits. Report SHA-256:
  `957abd20c4b1abd1693e587394902a4d8929db5300ddb3b94884aecede260ae4`.
- Read-only preflight of the retained complete capture receipt resolves all 73
  records to 73 unique portable destinations without copying any payload.
- Required native harness at the functional checkpoint passed 2,054 tests,
  eight existing SQLite warnings, 96.81% total coverage, 40 schemas/30 samples,
  9/9 parity, repository mutation lanes, dependency audit and licence checks.
  It then failed the secret scan on the test's literal alphabet (not a secret).
  Failure receipt SHA-256:
  `db35302d2ef040b5393267f92f829bed9198e1760e6d3d32b402f4be760e0b68`.
- Test-only checkpoint `26e5189` uses standard alphabet constants with the same
  character set. All 37 focused cases and the unchanged secret gate pass.
  The initial native run is not recorded as a full pass. Integrated assurance
  and hosted delivery will be recorded separately.
- Independent review found no remaining finding in this bounded path contract.

The plot recovery evidence accompanies this delivery: 67/67 mutants killed
after recovery, while the earlier timeout receipt remains intact. PR #274 and
Budget CLI/MCP PR #280 were observed merged by another actor; all seven checks
on the changed Budget head `199c82b49172d0c8dac67df3c528167ce16be98e` passed.
