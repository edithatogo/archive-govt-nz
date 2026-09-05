# Provisional post-P13 assurance

All execution evidence here uses software head
`9fe6894d5ba952aacaffa8bc05dc3f24ad4e2f08`. Prompt 15 was not integrated;
none of these results claims final Prompt 20 completion.

The complete harness stopped at tests: 4,799 passed, three failed, coverage
97.61 percent. Failures were two Hypothesis slow-input-generation health checks
and a five-second MCP subprocess timeout. The exact three tests later passed
serially without changes in 2.94 seconds. This distinguishes the isolated
results but does not turn the failed full harness into a success or establish
an exclusive cause. Downstream full-harness stages were not reached.

The existing parent-state mutation runner then passed its 108-test baseline and
all 46 mutants. Preserved logs contain no timing, health-check, collection, or
subprocess-timeout failures; these are ordinary assertion kills. Earlier failed
baselines remain in the parent directory. Temporary mutated Python files were
removed after preserving every log and the receipt.

The read-only actual-state benchmark independently checked the downloaded
GitHub artifact digest, bounded extraction, all 904 linked CAS objects with both
hashes, manifest/checkpoint consistency, and the reviewed 500-work scope
(852 records). Reconciliation reported zero mismatches and all 909 state files
were byte-identical afterward. Wall time was 2.994 seconds. Main-process peak
RSS was 142,852,096 bytes; child-process peak RSS was 134,578,176 bytes. Peaks
are reported separately and are not additive concurrent-memory measurements.
CPU and exact commands are in the receipt; the executed probe source is retained
as text with a hash. Artifact payload and extracted state were removed afterward.
No acquisition, public upload, or state publication occurred.
