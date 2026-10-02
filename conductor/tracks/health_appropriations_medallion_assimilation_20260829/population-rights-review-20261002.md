# Population export rights basis review — 2026-10-02

## Finding

The publisher's default reuse terms are observed for the national population
series: Stats NZ's copyright statement says its produced content is licensed
under Creative Commons Attribution 4.0 International unless otherwise
specified. The captured terms also exclude photos, graphics, logos, and
material with a specific copyright statement from that default. The Stats NZ
DataInfo+ record for National Population Estimates identifies Stats NZ as the
rights holder; the retained Infoshare export identifies table `DPE056AA`.

The resulting source-review state is
`publisher_default_observed_unadjudicated`. This is evidence of the publisher's
default and ownership, not a legal determination that this particular export
has no exception, not a grant of rights beyond the published terms, and not
approval to redistribute or publish the export or derivatives. Attribution
requirements must be carried into any later approved use. The population
Silver package and context Gold remain rights-unqualified, and the population
is not selected as a per-capita denominator.

## Evidence and limits

- [Stats NZ copyright terms](https://www.stats.govt.nz/about-us/copyright/),
  captured in the external Bronze CAS at SHA-256
  `6d4b02b53668bcdbac42bbb996cd63a624dd282eef6c3d4c803e36d9fd61e20f`.
  The external capture manifest records HTTP 200, observed time
  `2026-09-29T21:32:20.846127Z`, and WARC SHA-256
  `873cf9d358e3d8147c4c261f8e2e509a7b88db641b85bdce1d96d2fa2fcc9a53`.
- [Stats NZ DataInfo+ National Population Estimates](https://datainfoplus.stats.govt.nz/item/nz.govt.stats/4c9f3523-5386-4ce0-a8bd-993bb905f119/201)
  identifies Stats NZ as rights holder and describes both point-in-time and
  period-mean estimates.
- The existing 1,676-byte `DPE056AA` Infoshare export is pinned at
  SHA-256 `a52e0344d1b6e707de04b7b968f2667fc969c0f0777b319921ff716ead82a1d9`
  in the external CAS. Its earlier browser download did not retain HTTP
  headers or WARC, so this review does not upgrade that export's transport
  provenance.

No new population values were acquired, copied into Git, normalized, admitted
to analytical joins, or published. Historical revision coverage, status-flag
handling, fiscal-period alignment, denominator choice, and rights adjudication
remain open.
