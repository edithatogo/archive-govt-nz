# Legislation one-batch reconciliation correction

Replace the merged synthetic parity generator with a local, fail-closed
reconciler for one explicitly supplied real donor batch and its target
manifest, checkpoint, and CAS evidence. The implementation may be prepared
locally, but execution of a real batch remains ordered after the service,
global CLI, legislation CLI, MCP, and workflow corrections.

- [Requirements](./requirements.md)
- [Design](./design.md)
- [Plan](./plan.md)
- [Run log](./runlog.md)
- [Evidence](./evidence.md)
- [Review](./review.md)
- [Metadata](./metadata.json)

Parent issue: [#131](https://github.com/edithatogo/archive-govt-nz/issues/131)

