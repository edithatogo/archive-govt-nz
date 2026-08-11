# Self-review

Status: complete; no unresolved critical or high-severity finding.

## Findings and resolutions

1. **High — untrusted snapshot URL could become an arbitrary retrieval target.**
   Resolved by exact HTTPS `web.archive.org` validation, credential/port/path
   rejection, property tests, and a killed host-validation mutant.
2. **High — sequential external timeouts endangered the hosted job budget.**
   Resolved with bounded two-worker deterministic execution and shorter hosted
   request timeouts. The verified enabled run completed in approximately six
   minutes within the 30-minute job limit.
3. **Medium — Save Page Now success could be mistaken for captured content.**
   Resolved with the `submitted-pending-verification` state and later-run
   timemap/capture requirement.
4. **Medium — security fixtures triggered secret-scanner candidates.**
   Resolved by constructing credential-bearing test URLs without secret-like
   literals; the repository secret scan passes.

## Residual limitations

- Internet Archive availability and latency vary by runner and observation.
- GitHub artefacts provide 90-day operational retention, not permanent public
  preservation. Hugging Face durable backup publication requires a separately
  tested remote-write and reconciliation contract.
- Byte identity with a current official source is reported only when both
  objects are available and compared; otherwise the state remains unverified.
