# Local Fiscal analytical Gold package

The versioned package exports four separately typed tables from the verified
Fiscal spending-share, annual mean resident and household CPI benchmark queries.
Builds reverify the original objects, Silver/canonical packages and pinned
methodology observations. Nominal observations retain source amounts, canonical
IDs, original time-status labels, fiscal definitions and accounting qualifications.
Derived tables retain complete input lineage, formula policies and exclusions.

Native products contain 54 nominal, 162 share, 54 per-capita and 54 CPI benchmark
rows. Share exclusions are 47 missing denominators. Population exclusions are
18 unsupported March periods and two missing observations. They remain explicit.
No ISO currency, health-input-cost inflation, rights or publication claim is made.

Dry run verifies and serializes without writing. Write requires an exclusive new
output directory and rejects overlap with every input root, original or evidence
file. Partial failures retain bounded evidence. The manifest pins all four
Parquet payloads, row counts and query receipts. Readback requires an independent
manifest digest, exact inventory, bounded compressed/uncompressed sizes and exact
Arrow schemas. Only named tables and limits 1–200 are accepted. Package readback
proves product fixity; it does not repeat original-source verification.

Two package builds using retained source packages, each reverifying original
inputs, produced identical manifest and Parquet bytes. All typed tables read
back successfully and three original object digests remained unchanged. This
package replay does not claim fresh Bronze normalization; the three preceding
source-query PRs retain separate clean-room evidence. Native products and rebuild
recipe remain outside Git; the adjacent JSON receipt records their digests.

Nine focused tests exercise source verifier forwarding, nominal lineage,
repeat bytes, dry run, exclusive writes, input overlap, tampering, manifest pins,
symlinks, inventory and query bounds. Focused coverage is 86.81% with an 80% floor.
DuckDB views, plots/reports, CLI/MCP integration, Platinum/federation, scheduled
operations and whole-product recovery/final review remain open.
