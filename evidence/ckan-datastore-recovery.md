# CKAN DataStore recovery assessment

The 2026-08-01 CKAN probe contains a successful HTTPS `datastore_search` probe
for 44 Treasury resources, including 42 resources whose original URL was HTTP
and two already-HTTPS resources classified as restricted. The API endpoint is a
viable, secure fallback candidate for a separate structured capture lane; it is
not treated as proof that the original file or page is available.

No payload was transferred by this assessment. A follow-up capture must page
the API, preserve raw JSON responses, validate schema and rights, and record a
separate hash/version receipt. The remaining resources still require a
publisher-confirmed secure replacement or remain tombstoned/restricted.

Machine-readable receipt: `evidence/ckan-datastore-recovery.json`.
