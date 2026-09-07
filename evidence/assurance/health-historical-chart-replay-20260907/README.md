# Historical chart receipt reproduction on H

Base: `acf06c153c1f6900262da588c0308a57bb5dd985`. This corrects the replay
integration conflict without changing chart producers, package writers,
verifiers, source selections, original receipt pins or retained report bytes.

H producers add `workbook_inventory` to all four raw chart admission results.
The older expanded register intentionally pins the pre-inventory v1 receipts.
Serializing the complete H result therefore cannot satisfy those historical
pins. The recipe now explicitly calls `historical_chart_v1`, which:

- accepts only the four existing chart profiles and their exact v1 root fields;
- requires the expected schema, raw-context status, unassessed rights and
  non-analytical boundary, plus a workbook-inventory/v1 object with sheets;
- omits only `workbook_inventory`, without modifying the producer result;
- canonicalizes every historical field and checks the original supplied digest
  before returning the receipt to the unchanged strict selection join.

Unknown fields/schema changes fail closed. This is an explicit historical
projection, not a permissive serialization fallback or silent re-pinning.
Inventory contents are not part of the historical receipt's authentication
claim. Current packaged-output verification continues to use the complete
producer result and is unaffected. Source identity/fixity checks in producers
and the selection join are unchanged; modified retained fields fail the old
receipt digest. No capture, rights, Gold or whole-source coverage is inferred.

The new regression builds synthetic workbooks and invokes all four current H
producers (only synthetic source pins are substituted in these tests). It proves
projection bytes, input immutability, wrong-pin/source-digest rejection and
unknown/missing inventory or root-schema rejection. RED: 11 failures before the
helper existed. GREEN: 139 focused tests including the existing chart producer,
direct-coverage and expanded-coverage suites. Ruff and basedpyright pass.

Actual local commands, using the existing Python 3.14 environment:

```sh
PYTHONPATH=src python evidence/assurance/health-expanded-coverage-20260907/replay.py /Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations /tmp/health-crown-receipt-replay.iNn9fa/first
PYTHONPATH=src python evidence/assurance/health-expanded-coverage-20260907/replay.py /Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations /tmp/health-crown-receipt-replay.iNn9fa/second
```

These consume existing retained build receipts; they are not two new builds.
They reproduce the old report, not current H chart-package verification.
The local external inputs must be retained/restored with the same bytes. No
source payloads or new chart values are committed. The prior validation receipt
remains immutable and describes its original recipe digest; this follow-up
records the changed recipe digest separately.

No full harness, network, publication or parent edits were performed. Review of
this change is self-review only until the requested independent review returns.
