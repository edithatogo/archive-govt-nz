# Canonical Gold consumer example — 2026-10-02

The read-only example prints a compact structured summary after verifying the
exact package manifest digest and every declared output's fixity. Run it with a
canonical Gold package directory and its expected manifest SHA-256:

```sh
uv run --locked python tools/health_canonical_gold_example.py \
  /path/to/canonical-gold '<expected-manifest-sha256>'
```

The JSON output lists source-separated product counts, exact-context temporal
coverage counts, classification candidate count, and historical revision
counts. It does not aggregate observation values, infer missing periods,
interpret changed values, or join sources. Rights remain `not_evaluated` and
publication remains `not_performed`. Verification is bounded to the package's
manifest-declared output fixity; the example does not prove source completeness
or rights.

The focused contract test runs this against an offline package fixture and
checks that unresolved interpretation and release states remain explicit.
