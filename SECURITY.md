# Security policy

## Reporting

Report suspected vulnerabilities through GitHub's private vulnerability
reporting or security-advisory channel for `edithatogo/archive-govt-nz`. Do not
put credentials, personal information, exploit payloads, signed URLs, or
restricted source data in a public issue.

This is a solo-maintainer project. Reports are triaged by severity and available
evidence; no response-time promise is made. Acknowledgement, remediation, and
disclosure timing will be recorded without inventing a second reviewer.

## Security boundary

Archive inputs are untrusted. Retrieval and transformation must fail closed,
enforce explicit resource limits, quarantine suspicious content, redact
sensitive values, and keep credentials out of source, logs, fixtures, receipts,
and generated datasets. Publication requires separate local, upload, remote
verification, rights, and release gates.

Do not submit live secrets as test cases. Use unmistakably synthetic values.
