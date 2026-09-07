# PR415 final-followup assurance review

Requested verification passed for reviewed commit
`fcb8f7c89ffe18afd854f23f40c448fcc3a9efeb`, tree
`3b63cc340f93ce3b7dd813ab1259537926ce4bef`. This evidence delivery does not close
tracks or establish final programme deliverability: Popper peer acceptance has
not been supplied to this verifier and remains a separate gate.

## Independently observed results

| Gate | Result | Receipt |
| --- | --- | --- |
| Local real-state resources | Authenticated artifact 9970365066; all 904 objects verified, 500 works/852 scoped records reconciled with zero mismatches, all 909 state files unchanged. 2.037507333 seconds; process RSS 251,412,480 bytes and child RSS 135,430,144 bytes. | `resource-receipt.json`, `artifact-readback.json`, `resource-reconciliation.json` |
| Two reproducible builds | Separate clean git-archive exports of exactly fcb8f7c8; identical wheel and sdist; SOURCE_DATE_EPOCH 1788748146. | `reproducible-builds.json`, `build-1-receipt.json`, `build-2-receipt.json` |
| Supplementary hosted execution | Run 34076444101, attempt 1, exact head fcb8f7c8: all 11 jobs successful, all 11 authenticated ZIPs and execution receipts verified, all 113 payload-file sizes/hashes match exhaustive manifests. | `supplementary-artifact-verification.json` |
| Full three-OS hosted gate | Run 34076444097: Windows job 101603388600, Ubuntu 101603388847, macOS 101603388903 all successful, including their locked assurance steps. | `ci-three-os-readback.json` |
| Donor | Still archived, default main, HEAD 905f9e07c17af9d9d25dbe2b1c052fb8a290a4e3. | `donor-readback.json` |
| Security and ruleset | Paginated open CodeQL, Dependabot and secret-scanning lists empty. Ruleset 22180861 active, with strict required checks; documented maintainer bypass retained. | `security-ruleset-readback.json` |

CI's actual checkout was generated PR merge commit
`92410a99d6dd9b6c16fb924d3c6d88913d65ad4d`, not the branch SHA. Each independent
job-log readback identified that checkout, and the GitHub commit API confirmed
its tree exactly equals the reviewed tree. Log response hashes and checkout
parents are retained. This distinction is explicit; no Actions context or
hosted execution was fabricated locally.

Wheel SHA-256: `e376bb4a7c175cb89cf3d0f83217d86ece45eeb06c49feb3c0c881486eb332ad`.
Sdist SHA-256: `29d54ea012a62870cd649108de217d81fac8d9e2f357549c9a82a74eed8eae8d`.
The package/source-export bytes and build logs remain ignored scratch. This is
same-toolchain local reproducibility, not cross-platform package equivalence.

The resource check used the same declared local budgets as the retained probe:
60 seconds, 512 MiB per measured process high-water mark, 128 MiB expanded state,
1100 files. Time/RSS are assessed after execution, not imposed as hard OS memory
limits. Download time is excluded; RSS includes process lifetime and previous
child gh/git commands. Parent/child maxima are separate, not additive concurrent
memory. Builds ran after the resource measurement completed.

## Local harness and peer-review boundaries

Parent's retained `evidence/assurance/ordered-followup-20260907/local-validation.json`
records 5188 passing tests and 97.63953331231137% coverage on
`1f53a6e80873a99acc67c746fa6f1478b78b24aa`. Independent `git diff` confirmed the
only change from that commit to fcb8f7c8 is the new local-validation JSON itself.
This supports unchanged implementation; it is not relabeled as a local full
harness execution on fcb8f7c8. No full local harness was rerun here.

The visible GitHub review thread is resolved. Amazon Q's reported exception
syntax error is a Python-version false positive: the supported Python 3.14 parser
accepts the reviewed module. No production correction was required or made.
`review-readback.json` preserves the thread and resolution. That thread does not
establish Popper's acceptance; no Popper finding or approval is attested here.

## Retained attempts and reproduction

An initial pending three-OS snapshot remains in
`ci-three-os-observation-01.json`. The first completed-log verifier invocation
failed locally because gh refused terminal escape sequences. The original source
and failure are retained in `verify-ci-logs-attempt01.py.txt` and
`ci-log-readback-attempt01.json`. The corrected verifier permits capture only
for log GETs, publishes hashes/projections, and never prints or commits raw logs.
This was a readback correction, not a hosted rerun or a test-threshold change.

Run from a clean isolated checkout of fcb8f7c8 with these evidence scripts copied
into the same relative directory and existing authenticated GitHub read access:

```sh
uv run --locked python evidence/assurance/final-followup-20260907/resource-probe.py.txt
uv run --locked python evidence/assurance/final-followup-20260907/verify-builds.py.txt
uv run --locked python evidence/assurance/final-followup-20260907/verify-supplementary.py.txt
uv run --locked python evidence/assurance/final-followup-20260907/verify-hosted.py.txt
uv run --locked python evidence/assurance/final-followup-20260907/verify-ci-logs.py.txt
```

The completed-log verifier supersedes the simpler hosted metadata snapshot;
preserve earlier snapshots before a reproduction overwrites outputs. Scripts
are retained executable Python text, not production modules. Exact source and
receipt hashes are in the final file index and component receipts. Native
verifiers are the reviewed source versions. Source payloads stay in ignored
`.tmp`; no credentials, signed URLs or raw logs enter committed evidence.
No remote mutation, dispatch, merge, issue closure, track edit or registry edit
was performed. Earlier evidence directories remain untouched.

The final whitespace check flags one trailing empty line in each of the two
copied, executed resource/supplementary probes. These cosmetic warnings are
retained explicitly: trimming the executed bytes afterward would invalidate
their source-digest evidence. Probe syntax checks and the targeted secret scan
pass. No test, security or assurance threshold was changed for these warnings.
