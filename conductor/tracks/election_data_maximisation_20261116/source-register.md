# Election data sources: initial candidate and archive coverage register

**Inventory status: unverified planning register, 16 November 2026.** The archive's dataset card is a *coverage claim*, not proof of verified per-file or per-row completeness. Confirm publisher URLs, exact effective dates, document terms, and raw content hash before acquisition or promotion. `existing_claim` means documentation/code suggests material exists; `candidate` means source onboarding is proposed; `forthcoming` means availability must be checked after release.

| ID | Dataset / custodian | Time scope / update | Status to verify | Initial use / hold |
| --- | --- | --- | --- | --- |
| EC-F01 | [Electoral Commission party annual donations and loans](https://elections.nz/) | 1996–2025 claimed; annual filing, amendments | existing_claim | Bronze inventory, named/aggregate donation and loan accounting, source totals |
| EC-F02 | [Electoral Commission party election expenses](https://elections.nz/) | 2008–2023 claimed; election cycles | existing_claim | Separate regulated party campaign expenditure from annual finance |
| EC-F03 | [Electoral Commission candidate returns](https://elections.nz/) | 2011/2014/2017/2020/2023 claimed | existing_claim | Candidate spend/donation/loans with electorate identity and filings |
| EC-F04 | [Registered promoter expense returns](https://elections.nz/) | 2020/2023 claimed; 2026 when filed | existing_claim/forthcoming | Independent advertising and double-counting controls |
| EC-F05 | [Major donations over NZ$20,000](https://elections.nz/democracy-in-nz/political-parties-in-new-zealand/donations-exceeding-20000) | 2026 and historical postings; check daily | candidate | Current disclosed flows; later annual-return reconciliation |
| EC-F06 | [Party annual financial statements](https://elections.nz/democracy-in-nz/political-parties-in-new-zealand/annual-financial-statements) | Periodic annual; years require census | candidate | Organisational revenue/balance-sheet context |
| EC-F07 | [2026 broadcasting allocation](https://elections.nz/guidance-and-rules/for-parties/about-the-broadcasting-allocation/broadcasting-allocation-for-the-2026-general-election) | 2026 allocations and revisions | candidate | Allocations separate from actual broadcast advertising spending |
| EC-F08 | [2026 promoter register](https://elections.nz/) | Live 2026 registration and amendments | candidate | Registered promoter identities; registration not evidence of spend |
| EC-E01 | [NZ official election result portal](https://electionresults.govt.nz/) | 1996–2026, preliminary/official, append-only | existing_claim | Source-verified votes, electorate seats, statutory allocation and special votes |
| EC-E02 | [Voting-place and detailed returns](https://electionresults.govt.nz/) | 2017/2020/2023/2026 captured subsets | existing_claim | Reprocess already archived raw CSVs; per-place parity and coverage |
| EC-E03 | [Electoral Commission enrolment and advance voting](https://elections.nz/) | 2008 onward partly documented; 2026 captured | existing_claim | Turnout/registration and advance-vote time series |
| GEO-01 | [Stats NZ electoral boundaries / datafinder](https://datafinder.stats.govt.nz/) | 2002, 2007, 2014, 2020, 2025 review vintages claimed | existing_claim | Valid-vintage crosswalks and spatial joins; preserve key/access terms |
| GEO-02 | [Stats NZ 2023 Census](https://www.stats.govt.nz/2023-census/) | Census plus later demographics | existing_claim/candidate | Geographic and population-weighted context, no ecological causal leap |
| POLL-01 | [Wikipedia NZ general-election opinion polls](https://en.wikipedia.org/wiki/Opinion_polling_for_the_2026_New_Zealand_general_election) | 1993–2026 raw wikitext/HTML captured | existing_claim | Normalisation and original pollster-method verification; CC BY-SA obligations |
| POLL-02 | [New Zealand Election Study](https://www.nzes.org/) | 1993 figshare claimed; further waves candidate | existing_claim/candidate | Weighted voter preference/attitude research; licence and access check |
| ADV-01 | [Meta Ad Library](https://www.facebook.com/ads/library/) | Date/platform dependent | candidate | Political advertiser/creative and spend bands; platform coverage limitations |
| ADV-02 | [Google Ads Transparency Center](https://adstransparency.google.com/) | Date/platform dependent | candidate | Political advertising and interval expenditure; method/rights assessment |
| ENT-01 | [Companies Office / NZBN](https://www.companiesoffice.govt.nz/) | Business registrations and changes | candidate | Corporate donor identity resolution; false-positive review |
| ENT-02 | [Charities Services register](https://www.charities.govt.nz/) | Current/historical public records | candidate | Organisational identities and annual-return context |
| LOC-01 | [DIA local authority election statistics](https://www.dia.govt.nz/) | 2004–2025 published sets / partial captured | existing_claim/candidate | National/local electoral comparisons with different rules |
| PAR-01 | [NZ Parliament](https://www.parliament.nz/) | Members, interests, bills, divisions, Hansard | candidate | Post-election research; no inference of donor influence |
| GOV-01 | [NZ Government Procurement](https://www.procurement.govt.nz/) | Award and procurement notices over time | candidate | Organisational research context; no allegation from linked entities |

## Filing calendar to monitor (not proof of availability)

- **7 November 2026:** preliminary election results published; preserve their source vintage.
- **27 November 2026:** Electoral Commission official declaration expected; discover and validate before public vintage switch.
- **December 2026:** detailed E9/voting-place release expected; verify publication date and inventory.
- **9 March 2027:** candidate financial returns due.
- **8 April 2027:** party election-expense/broadcasting returns due.
- **30 April 2027:** annual 2026 party donation/loan returns due.

Filing due dates are not publication timestamps. For each source, register actual published/revised/captured dates; keep 2026 expenses unavailable until independently evidenced. Refresh proposals: election results daily/hourly close to declaration; immediate donations daily; filings daily around due windows and weekly otherwise; archived sources weekly/monthly reconciliation. No scheduled workflow is activated by this file.

## First admission and validation actions

1. Enumerate exact existing original CAS object IDs and receipt hashes per record family; check raw access, deduplication, licences and missing expected-file denominators.
2. Compare each `materialize_parquet.py` output's source lineage against official return totals; mark hard-coded/demo figures `synthetic`, not historical Silver.
3. Cross-check the HF archived dataset's queryable table structure and failing viewer against separately verified raw bytes; do not infer absence or completeness.
4. Prioritise eligible source additions EC-F05 to EC-F08; subsequently digital ads and entity directories. Preserve input/rights review as a decision checkpoint, not automatically approved crawling.
5. Recheck authoritative 2027 statutory dates and historical thresholds at execution; store effective-dated rules rather than hard-coded cap literals.

## Source-specific risks

- Disclosure thresholds and reporting categories change; all-donor distributions often cannot be recovered from published named disclosures.
- Political advertising spend may be reported in intervals, subject to missing platforms or changing eligibility definitions.
- Automatic donor-company or donor-MP joins can create politically consequential false positives; publish only substantiated identities with uncertainty and correction process.
- Source public accessibility does not itself grant unrestricted bulk redistribution; record original licensing and any dataset-specific restrictions.
