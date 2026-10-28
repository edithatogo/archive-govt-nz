# Metadata contract completion audit — 2026-10-28

Objective: complete the remaining Phase 7.1 metadata contracts, including schemas,
standards profiles, mixed/resource licensing and fail-closed release readiness.
This is not a whole-Phase-7 completion or external publication task.

## Completion requirements and current evidence

| Requirement | Current evidence | Remaining proof/work |
| --- | --- | --- |
| Versioned schema-as-code for admitted metadata | Rights assertion v1 and verification receipt v1 schemas exist | Validate remaining metadata/profile envelopes and representative positive/negative fixtures |
| DCAT, Croissant, RO-Crate, PROV application profiles | Gold, candidate and qualified headline projectors; offline RDF tests; scoped reconstruction | Complete explicit profile contracts, actual field/source bindings and independent offline standards checks; separate local inventory validity from publication conformance |
| Estate/dataset cards, catalogue and citations | Gold and qualified discovery builders reconstruct pinned outputs | Bind contract-level claims and rights to supplied resources and report unsupported profiles |
| Mixed/resource licensing | metadata_application validates v2 inventory assertions and supplied evidence fixity; qualified overview binds approved narrow source evidence | Cover every included derivative and metadata member; reject missing/conflicting/incompatible grants without blanket inheritance |
| Release readiness integration | Legacy verify_candidate checks hashes and original rights; synthetic positive uses empty metadata dictionaries | Integrate metadata/profile and all-resource rights qualification; demonstrate qualified positive and missing/conflicting/unsupported negatives without granting publication approval |
| Original/historical stability | Existing products/reviews/candidate publication are retained | Prove new validations do not rewrite old bytes or inherit historical publication authority |
| Assurance and reconciliation | Existing focused/full/hosted evidence for prior slices | Focused contract tests, required full harness once reviewable, protected PR delivery and requirement-by-requirement completion audit |

## Initial actionable finding

`verify_release_readiness` currently returns success for a hash-consistent legacy
candidate whose Croissant/DCAT/PROV/RO-Crate payloads are `{}`. Its rights check
covers originals but not derived outputs. The separate generic publication/v2
metadata validator is not connected to that path. Candidate inventory generators
correctly leave rights and standards qualification blocked. Fix integration rather
than trusting manifest gate strings or replacing historical candidate bytes.

Primary standards references: MLCommons Croissant 1.0 specification,
https://docs.mlcommons.org/croissant/docs/croissant-spec.html;
RO-Crate 1.1, https://www.researchobject.org/ro-crate/specification/1.1/;
W3C DCAT 3, https://www.w3.org/TR/vocab-dcat-3/;
W3C PROV-O, https://www.w3.org/TR/prov-o/.

Remaining unproven rows stay open until their stated proof is retained. Missing
source rights may produce a correctly blocked contract result; it must not be
reported as release eligibility or bypassed by a schema/conformance assertion.

## Isolated SDK evaluation remains unqualified

`mlcroissant` 1.1.1 installed on the isolated Python 3.15.1 evaluation runtime;
it is not adopted in the repository lock. Three synthetic, network-denied static
analysis probes are retained. The first rejected the HTTP schema.org Dataset
namespace. The second encountered missing default-language context handling.
The third proceeds to seven validation errors involving conformsTo/version
recognition, FileObject type selection, mixed-rights notice representation and
the supplied fictional dataset name; two recommendations concern citation and
semantic-version syntax. No values are cast or silently renamed to force a pass.
The latest prototype explicitly uses a neutral null default language and the
HTTPS contentUrl property. It is not yet qualified for SDK loading or final
standards-profile completion. Preserve these failures and finish the remaining
independent graph/negative contracts before the original goal can close.

The separate product-coverage PR #804 is on integrated head `30095507` and
awaits required hosted platform assurance. Its inventory-only discovery claims
remain distinct from this unfinished release-contract prototype.
