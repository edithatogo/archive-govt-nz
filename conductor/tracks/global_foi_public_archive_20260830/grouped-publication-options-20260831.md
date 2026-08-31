# Proposed reusable publication decisions

Status: **options for user review; no group is approved by this document**.
The user's public-archive intent is already authorized. The remaining decision
concerns defensible source/content boundaries and privacy handling, not permission
to perform every ordinary upload. Source rights cannot be created by operator
approval. Any decision must be recorded attributably against this policy version.

## Recommended: conditional standing policy, with quarantine exceptions

Approve publication of current and future snapshots that satisfy the applicable
policy group and the exact source/resource scope. Record an automated, hash-bound
eligibility receipt for every snapshot; do not ask again merely because its bytes
or capture date changed. A new origin/resource triggers documented agent admission checks, not an
automatic human approval request. Uncertain rights or provenance, a new data
category, sensitive content, conflicting terms or a takedown require human
review. Licence/schema changes require fresh conformance evaluation; uncertain
or out-of-category changes remain quarantined. Preserve originals
privately while assessing exclusions. Do not silently modify a raw original and
continue calling it the original: any redacted public derivative has a separate
identity linked to its retained original.

| Group | Proposed reusable permission | Evidence and exclusions |
|---|---|---|
| `institutional_open_data` | Public source-issued statistical/institutional originals and metadata with an explicit redistribution licence or documented public-domain basis, required attribution and a validated non-personal schema. | CA ATI nil returns are the initial candidate. Personal data, requester correspondence, case names/narrative annexes, third-party works, credentials, seals/logos and licence exceptions are excluded. US annual statistical XML requires separation or review of narrative/case-title fields before the complete original qualifies. |
| `mixed_correspondence` | Permit metadata and eligible content under a reusable source-specific rights/privacy rule once that rule is evidenced. No automatic approval from website visibility. | NZ FYI request pages, correspondence and attachments retain several possible rights holders. Public availability and the site's takedown policy do not supply a blanket third-party licence. A source-wide rule can replace per-file approval only where its authority and exceptions are defensible. |
| `restricted_or_unclear` | Publish only approved non-sensitive source/disposition metadata; retain payloads privately where access/retention is permitted. | Do not activate public payload publication while licence, personal-information, access or takedown restrictions remain unresolved. Restrictions stay visible in country denominators. |

An alternative narrower decision would approve only the current CA nil-return
candidate after review, with every other raw candidate pending. An alternative
metadata-only decision would leave every raw group unapproved. The conditional
standing policy avoids repeated approvals while retaining explicit exclusions.

## Primary evidence

- [Canada dataset](https://open.canada.ca/data/en/dataset/0797e893-751e-4695-8229-a5066e4fe43c): the retained CKAN response declares `ca-ogl-lgo`; its description excludes requests focused on personal or third-party proprietary information and notes incomplete institutional participation.
- [Open Government Licence Canada](https://open.canada.ca/en/open-government-licence-canada): redistribution is permitted with attribution, subject to exclusions including personal information and third-party rights. Default attribution is “Contains information licensed under the Open Government Licence – Canada.” Link the licence; imply no endorsement.
- [DOJ legal policies](https://www.justice.gov/legalpolicies): unless otherwise indicated, DOJ website information is public domain and may be copied/distributed; third-party material and official seals/logos are exceptions. This is evidence for a bounded DOJ resource, not all US documents.
- [DOJ FY2025 annual report](https://www.justice.gov/oip/department-justice-annual-foia-report-fy-2025): links the captured XML statistical report. Inspection found narrative and case-title fields, so public-domain evidence alone is not a complete privacy screen.
- [FYI privacy](https://meta.fyi.org.nz/help/privacy/) and [officers/copyright](https://meta.fyi.org.nz/help/officers/): the service supports public access and takedowns; these pages do not establish a blanket downstream redistribution licence.

## Required implementation and accountability

A standing decision records policy ID/version, accountable reviewer/date,
source/resource allowlist, lawful rights basis, attribution, prohibited fields,
privacy-screen rules, licence/schema drift checks, takedown handling and expiry or
review trigger. A subsequent snapshot receipt binds source bytes, original/derived
identity, policy version, checks/results and public destination. The decision is
not a claim that automated screening detects every personal-information risk.

Takedown handling must address current pointers, historical public revisions and
mirrors/caches where controllable, with a minimal public tombstone and private
incident evidence. Do not claim complete removal merely because the current index
no longer links to a still-public object. Existing NZ pending package approvals
remain unchanged, and no synthetic review identity is attributed to the user.

## Concrete initial allowlist and remaining engineering gates

The companion JSON pre-fills the exact CA resource URL, licence/attribution,
allowed public files and exclusions. **Only `ati-nil.csv` and reviewed derived
index/manifest are initial public candidates.** The full original CKAN
`source-metadata.json` remains private: provider contact/free-text fields have not
been cleared. The source schema and licence evidence also remain private unless
separately reviewed for publication.

A proposed list of the current organisation identifier/title pairs has been
preserved privately and hash-bound in the policy JSON for an initial agent
evidence-based conformance review under the proposed standing policy. This review
is still pending. Straightforward official, non-personal organisation pairs do
not require a second human approval; ambiguity about identity, personal information
or rights is escalated to the user. Completed agent checks must be attributed to
the agent, never presented as user review.
The adapter currently checks identifier syntax and title length, not whether a
free-text title contains personal information. Before standing-policy publication,
the publisher must reject new or changed identifier/title pairs relative to the
reviewed allowlist. New or changed pairs remain quarantined until an agent
conformance check establishes the same official, non-personal category; ambiguous
cases require human review. Future matching institution-month rows can then follow the
same standing decision without repeated per-file approval. A changed organisation
name triggers that agent check, not automatic clearance or mandatory human approval.

The JSON explicitly separates implemented preservation/schema checks from pending
publication enforcement. Numeric-looking values in US XML are not proof that the
associated field or context is non-sensitive. The complete US XML and all narrative
fields remain private; a reviewed aggregate-field projection is still required.
An umbrella policy decision alone does not approve NZ or other mixed correspondence.

## Delegated admission within the approved institutional category

After the user approves the standing policy, the archive agent may admit new
official institutional/statistical sources without separate human approval when
primary-source evidence establishes official provenance, applicable redistribution
rights, attribution and conformance with the approved non-personal category.
Official/public availability alone is insufficient. Admission records exact
resources, schemas, privacy checks, exclusions and evidence hashes.

Resource allowlists are outputs of successful admissions and runtime constraints,
not a mandatory new human decision for every URL. Agent-authored admission receipts
link to the user-approved policy; they must not impersonate user review or imply
legal certainty. New origins trigger these checks. Ambiguous rights, provenance,
personal information, narratives, unlicensed third-party works or new data
categories return to human review. Numeric syntax alone proves no privacy outcome.

The standing policy still requires user approval, and the initial Canadian
agent conformance review remains pending rather than implicitly completed by this
document. Complete US XML and NZ correspondence remain excluded. Admission enforcement
and public-file filtering remain required implementation before any upload.

The proposed initial public destination is the Hugging Face dataset
`edithatogo/foi-ca-federal-atip` (not created or verified). A separate public
manifest must enumerate only the allowed published CSV and derivatives; the
private pilot package manifest is not an upload-ready public manifest. Anonymous
restore must verify every published member before any public completion claim.
