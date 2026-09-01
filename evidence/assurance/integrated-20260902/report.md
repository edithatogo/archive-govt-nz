# Prompt 20 integrated assurance report

The selected integrated target is
`dd90f8ec01c91290895e9f2a684d948a520b0f1f`. The archived donor remained at
`b40587f1b1aec7356a0f623916fcc8212397d283` throughout verification.

The clean local harness passed all 31 registered stages: 4,543 tests, 97.50%
project coverage, 48 schemas and 38 representative documents, 9/9 parity
cases, every registered mutation suite, dependency audit, licence inventory,
secret scan, CycloneDX SBOM, and the 438.44 MB/s CAS benchmark. The exact-main
hosted CI run `33545341871` subsequently passed on Ubuntu, macOS, and Windows;
CodeQL analysis run `33545341907` and workflow-policy run `33545341876` also
completed successfully.

Additional cold mutation runs killed 34/34 parent-state restoration mutants,
26/26 durable-state/readback mutants, 9/9 evidence-index mutants, 15/15
release-correction mutants, and 9/9 donor-bundle mutants. Two isolated builds
with `SOURCE_DATE_EPOCH=1788288217` produced byte-identical wheels and source
archives. Five offline resolutions of the exact reviewed 500-ID seed all passed
and returned identical output. No live acquisition, state merge, or continuation
was dispatched because the Prompt 13 parent/no-write lane remains blocked.

## Blocking findings

The acceptance criteria are not met:

- Code scanning has two open high-severity
  `py/incomplete-url-substring-sanitization` alerts at the exact integrated
  head, including production code. Issue #352 owns remediation.
- actionlint 1.7.12 exits 1 with SC2086 findings in two workflows. Issue #353
  owns remediation.
- `main` has no branch protection or applicable repository ruleset, so passing
  checks are not hosted enforcement. Issue #354 owns the hosted-settings gate.
- Standalone zizmor was unavailable. The repository workflow-policy equivalent
  passed, but it does not erase the actionlint failures.

Prompt 6 and Prompt 7 have no merged implementation. Prompt 10 remains a draft
PR and is absent from the integrated head. Prompt 13 contributes truthful
blocked evidence rather than operational success. These facts are inventory
boundaries, not retrospective success claims.

## Preserved failed attempts

- An actionlint command using both `*.yml` and nonexistent `*.yaml` shell globs
  failed before linting because zsh rejected the unmatched glob. The rerun used
  null-delimited `find` input and exposed the two substantive findings.
- The first hosted-alert query left `?` and `&` unquoted and zsh rejected it as
  a glob. Quoted endpoint reruns returned the exact open alert inventory.
- A 20-iteration seed timing process exceeded the local 30-second execution
  window before emitting a receipt. The bounded five-iteration rerun completed
  and is retained without presenting it as a live 500-work harvest benchmark.

No thresholds, workflows, production logic, hosted settings, donor state, or
external publication state were changed by this assurance issue.
