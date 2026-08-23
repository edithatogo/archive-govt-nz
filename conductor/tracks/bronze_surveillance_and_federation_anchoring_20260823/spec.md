# Specification: Surveillance Heartbeat Ledger & Cross-Repository Federation Protocol

## Architecture
```text
[Surveillance Ingestion Loop]
      │
      ├──> HTTP 304 / ETag Match ──> [Strata B0 Heartbeat Log (Append-Only JSONL/Parquet)]
      │                                    │ (Zero B2 CAS write amplification)
      │
      └──> HTTP 200 / Modified ──> [Standard Medallion Pipeline]
                                           │
                                           ├──> [Canonical URN Injection]
                                           │        (urn:nz:health:pharmac:...)
                                           │
                                           └──> [Weekly Merkle Root Generator]
                                                    │ (Asynchronous Sidecar)
                                                    ▼
                                            [OpenTimestamps Anchoring (.ots)]
```

## Federation URN Syntax
`urn:nz:<domain>:<agency>:<year_month>:<type>:<identifier>`
Examples:
- `urn:nz:legislation:pco:2005-04:act:dlm12345`
- `urn:nz:gazette:dia:2026-01:notice:2026-0012`
- `urn:nz:health:pharmac:2026-08:schedule:98765`
