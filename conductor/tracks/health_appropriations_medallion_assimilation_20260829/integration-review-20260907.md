# Ordered health and FOI integration

The locked full repository harness passed on implementation commit
`e363eaffdc4d9e64bad32cf4b0093b73b9ca0b3f`: 5,363 tests, schema/parity,
all configured mutation suites, dependency audit, licence inventory,
credential scan and validated SBOM (112 components). CAS throughput was
670.31 MB/s. This receipt does not establish hosted delivery or clear rights.

Independent review found a generated-column schema bypass in the new donor
oracle. A red regression reproduced the acceptance of a virtual generated
column. Fix `82d8ba93b7b498ebb4aa9926248f02be43bcf978` uses `table_xinfo`
and requires the ordinary-column hidden flag. All 22 oracle tests pass;
independent re-review confirms rejection before the row query. The recorded
real donor replay is unchanged. Integration must rerun the full gate with
this fix before delivery.

The parallel FOI review found per-redirect crawl-delay enforcement, successful
page/terminal transport binding, and finite timeout-validation gaps. These
remain delivery blockers until fixed and re-reviewed. Prior observations are
historical evidence, not a claim that every collector policy was met.

Health and FOI tracks remain active. No publication, semantic repair approval,
schedule activation or terminal track acceptance is asserted here.
