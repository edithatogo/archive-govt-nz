# Donor Git bundle verification

Observed on 2 September 2026 against target `main`
`b89df7e8f44031d892d014108deec9570f5d8755` and the archived donor
`edithatogo/corpus-legislation-nz` at
`b40587f1b1aec7356a0f623916fcc8212397d283`.

The authenticated target release API returned draft release `377118888` and
asset `530775782`. The downloaded 2,365,303-byte asset has SHA-256
`f125f91b06264a97e59f65fac47878a74d646c915f12c0b05841c1550ec741c2`,
which equals both the audited value and the hosted asset digest.

`git bundle verify` reported a complete bundle. A mirror clone and an
independent bare-repository fetch of every bundled ref both passed `git fsck
--full --strict` without output. The normalized live and bundle advertisements
match at every name and object ID: `HEAD`, 3 branches, 1 tag, and 119 pull head
refs (124 entries total). The restored graph contains 2,969 reachable Git
objects and 331 commits. The final `main` tree is
`0e892d5aa6c9c6225c75112a15040b6bd6fab043`.

The final tree retains the repository licence, notice, citation, dataset card,
README, 25 workflow files, and 216 Conductor files. It contains no tracked
`.gitmodules`, gitlinks, `.gitattributes`, or Git LFS pointer blobs. LFS syntax
occurs only as generator template text and does not create an external restore
dependency. GitHub independently reports the final commit signature as valid;
the bundle retains signed commit objects, while local trust verification remains
dependent on an independently governed keyring.

This is a complete Git-native copy of all objects reachable from the donor refs
advertised at observation time. It does not preserve GitHub issue or pull-request
discussion, Actions logs or artefacts, repository settings or secrets, releases,
hidden refs, reflogs, unreachable objects, or external dataset bytes. The asset
is still on a mutable unpublished draft release, so it is a verified gated backup
rather than a public, immutable, or independently durable preservation copy.

## Failed attempts retained

- The first release-list query requested an unsupported `databaseId` field and
  failed before changing state.
- The first download command was rejected locally because it included a
  destructive cleanup operation.
- The first authenticated asset response was refused by `gh api` because escape
  sequences were not explicitly allowed; it produced a zero-byte file. The
  successful retry used `--allow-escape-sequences`, followed by exact size and
  digest verification before Git inspected the bytes.

No release was published, no asset was moved, and the donor was not unarchived,
edited, tagged, or re-archived during this verification.
