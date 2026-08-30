# Global FOI discovery catalogue

Build a local candidate with:

```sh
uv run --locked python tools/build_foi_catalogue.py --output build/foi-catalogue-candidate
```

The builder verifies pinned donor registry and geographic snapshot hashes, then emits source, geographic and jurisdiction JSONL indexes, JSON/Markdown coverage reports and a SHA-256 manifest. It refuses to replace different candidate files. It does not fetch requests, schedule captures or upload anything.

The universe contains 248 UN M49 countries/areas, two explicitly identified project jurisdiction extensions (TW and XK), and the EU as a separate supranational entity. UK, Scotland and New Jersey aliases reconcile geography without losing the declared source jurisdiction. Inclusion is not a sovereignty assertion. The universe URL, observation time and source HTML hash are recorded in country-universe.json.

All 23 runtime instance identities, six additional sites and 42 regime targets retain donor provenance. Every geographic entity is represented, but sources absent from these seeds remain discovery_required, not proven unsupported. Request denominators remain null. All raw capture, raw publication and completeness claims remain false until separately verified. Recorded HF revisions reflect anonymous repository metadata observations only and must be refreshed before publication promotion.

This is source-discovery metadata, not the request/correspondence/attachment/object metadata index required in Phase 3. Rights and privacy assessment, origin pacing, full source discovery, raw preservation, public restore and scheduler takeover remain open in the governing track. In particular, the donor's separate AU/NSW private-retention workflow is not converted to a public destination by this catalogue.
