# Independent local preservation recheck

Observed2026-08-31T15:29Z. This read-only audit used streaming SHA-256 and
byte counts, then parsed each WARC response and checked its payload against
the captured CAS identity. It did not rerun extraction, contact sources or
Hugging Face, qualify rights, alter originals, or approve a candidate.

| Scope | Entries verified | Bytes verified |
| --- | ---: | ---: |
| Complete-capture CAS originals |73|38,877,606|
| Complete-capture WARC receipts |73|38,915,034|
| Donor manifest objects |23|6,604,301|
| Listed v4candidate files |94|39,390,246|

These are overlapping collections, not additive unique-byte totals. All73WARC
files contain exactly one response; each decoded payload has the same SHA-256
and length as its captured original. There were no missing or mismatched
objects. The94candidate entries exclude the root candidate manifest itself,
whose independent pinned digest was also verified.

Pinned complete-capture manifest:
`04145e4030bfddaecade1af542e12cb8a56a187c9c924b7a4c135537ccae9dab`.
Pinned v4candidate manifest:
`9a33babda857b0aa7c60a6012000cf1e730fed729781cb8ceb6e7a4714cae40e`.
Observed donor manifest:
`893f387e1f361400285ccc84802b497e87802d1ad913826ff7d9055b07a03b74`;
this audit checked its internal file count, total size and object identities,
but did not independently pin the donor manifest from Git or reconstruct the
donor Git tree. The donor's prior pinned snapshot evidence remains separate.

Local audit script SHA-256:
`a364465d8191795d427c8e7e5ec3bbba647c626e52bfb73db8570b68862fc335`.
The script is retained outside Git at
`/tmp/health-compatibility.qDiHHO/preservation-audit.py`. Its output contains
aggregate evidence only; no original payloads or source metadata are committed.

This does not establish complete historical coverage, semantic validity of
every source, future disk state, or the current state of remote HF bytes. New
source-specific and canonical derivatives are not implicitly included in the
older v4candidate or its publication approval.
