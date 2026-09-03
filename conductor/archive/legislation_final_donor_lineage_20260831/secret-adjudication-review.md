# Public import-path candidate review — 2026-08-31

The hosted secret gate at `4aba7cb` rejected 99 Base64 entropy candidates after
2,167 tests passed on each platform. All 99 candidates were independently
verified as public commit-addressed import paths in four target-authored lineage
JSON documents. Imported donor bytes and existing receipt hashes are unchanged.

The correction retains the original scanner report and writes a separate
`build/secret-adjudications.json` report. An adjudication requires the exact
reviewed document SHA-256, detector, allowed JSON key, known donor revision,
import-path shape, line number and candidate-value hash. No file/line exclusion
was added and no scanner threshold changed. Document mutations fail closed and
require new review. Other candidates on the same line remain unresolved.

Validation: 11 focused supply-chain tests passed; targeted strict typing, whole
tree Ruff format/lint and Conductor (71 tracks) passed. Regressions cover a
second candidate on the same line, document drift, wrong detector/file/key/
revision/line, Windows paths, missing files and malformed scanner records.
The unchanged exact secret command passed with 99 retained original findings,
99 separately adjudicated paths and zero unresolved candidates.

One required native `./scripts/validate.sh` attempt used ctrace, disabled JIT and
four workers. Pretest gates passed. The test stage reached 80% and displayed a
failure marker before its unchanged 300-second deadline, exit 124. No final
summary or traceback identified that failure; this is not a full-suite pass.
Post-test stages were not reached in that attempt. No limits were relaxed;
hosted validation of the revised commit is still mandatory before merge.

- Native log SHA-256: `1ce1ceb070010e5d87e1b6053e1cc97ea4c2f74292bbc633b6095f22a1784e21`
- Original scanner report SHA-256: `d4766ac6133807261e671d796832f3cba25b6858c32a194c99b4b73d4d54830a`
- Separate adjudication report SHA-256: `9a914a605e07e2d841af5d05d23aa89b8e81c512755f8c63ab0ba9fa72167c3d`

No acquisition, payload import, publication, donor retirement or release action
is represented by this scanner correction.
