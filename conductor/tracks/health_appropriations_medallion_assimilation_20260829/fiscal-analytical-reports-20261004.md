# Fiscal analytical reports — 4 October 2026

The companion report package contains six discrete-point plots, exact structured
results, Arrow schema descriptors, a dataset card, PROV and DCAT JSON-LD, and a
pinned manifest. It preserves accounting, GST and fiscal-period distinctions;
missing denominators remain explicit exclusions. Household CPI remains a
purchasing-power benchmark, not a health input cost deflator. No ISO currency
code is asserted.

The CLI defaults to dry-run. Explicit writes require a new output directory and
reject overlap with input Gold. Written packages are read back immediately.
The standalone verifier checks the exact twelve-file inventory, eleven payload
hashes and byte-identical metadata projections. It does not reverify original
sources or establish report semantic correctness independently of the pinned
producer. Rights are not evaluated and publication is not performed.

Native evidence: two retained builds have all twelve files byte-identical;
257 plotted values and 67 exclusions independently match direct Arrow reads.
The input Gold package is unchanged. Actual CLI dry-run, write and verifier
commands passed. Both JSON-LD documents parse offline using inline contexts;
focused tests independently check typed DCAT checksums and provenance edges.
The nominal PNG was visually inspected for legibility. See the machine receipt
for manifest and recipe hashes and the external evidence location.

This bounded report delivery does not close full Platinum federation, scheduling,
whole-product recovery or final Health track review. Refs #212 and #213.
