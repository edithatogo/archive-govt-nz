# Architecture Specification: Legal Document Identity and Versioning

**Scope**: Functional Requirements for Bibliographic Records (FRBR) applied to NZ Legislation.

---

## 1. Entity Layering

1. **LegislationWork**: The abstract statutory entity (e.g. `work-act-1989-107` for the Public Finance Act 1989).
2. **LegislationExpression**: The state of a work at a specific temporal point (e.g. `expr-1989-107-v2024-01-01`).
3. **LegislationManifestation**: The physical document format (`text/xml` or `text/html`) pinned by content hash.
4. **LegislationItem / NormalisedRecord**: The parsed, queryable structured record in Parquet/JSONL.

---

## 2. In-Force & Repeal Semantics

- **Status Transition**: Tracks `in_force`, `amended`, `repealed`, and historical states with commencement dates.
- **Amendment Tracking**: Cross-links amendment acts to target principal legislation.
