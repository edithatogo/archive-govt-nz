# Evidence

- Target baseline: `6755e12a48536de938b6f5955fe974d4b1de1b75`.
- Archived donor head: `b40587f1b1aec7356a0f623916fcc8212397d283`.
- Canonical index: `evidence/migrations/corpus-legislation-nz/evidence-index.json`, 183 hash-bound entries plus one explicitly derived evaluator output.
- Corrected closeout: `docs/migrations/corpus-legislation-nz/corrected-closeout.md`.
- Historical evaluator output remains byte-identical at SHA-256 `81219add4c2bd0c754484993567a6ffdc0762db692a909b724001a4ab0911aee`.
- Current evaluator result: code/capability complete; operational state incomplete; custody/recoverability externally blocked; publication identity externally blocked; overall incomplete.
- Focused critical validation: 45 tests passed with 100% line and branch coverage for both changed critical modules; 9/9 targeted mutants killed.
- Full repository tests: 4,496 passed at 97.50% coverage. Forty-six schemas, 36 representative documents and 9/9 parity checks passed. All configured repository mutation lanes passed.
- Dependency audit: one standalone run passed with no known vulnerabilities. Later full-harness and standalone attempts recorded repeated external OSV HTTP 500 responses after all preceding lanes passed.
- Supply-chain controls: the secret scan passed after exact adjudication of one public checksum pathname; the SBOM validated with 111 components; the licence inventory passed.
- Final local harness rerun: 4,497 tests passed at 97.50% coverage after one preserved Hypothesis deadline flake passed in isolation. Every subsequent lane passed through the CAS benchmark; OSV again returned HTTP 500 on all three audit attempts.
- Post-review final harness: 4,501 tests passed at 97.53% coverage; schemas, parity, all configured mutation lanes, hygiene, CAS benchmark, dependency audit, licences, secret scan, and the 111-component SBOM all passed end to end.
- Hosted exact-head validation: PR #346 head `fcf99b635e52ba62b984a17a1990c1c02c46c0e6` passed CI assurance on Ubuntu, macOS, and Windows (run `33529173734`), CodeQL (run `33529173703` plus CodeQL status check), dependency review (`33529173723`), workflow policy lint (`33529173646`), and Amazon Q Developer.
- No external dataset, metadata, DOI, release, donor state, or publication surface was changed.
