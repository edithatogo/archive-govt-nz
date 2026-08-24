# Requirements: Assimilation Parity Gate Hardening

## Background
The HathiTrust NZ and Medico-Legal assimilation tracks name their donor
repositories and reusable assets but do not pin donor commits or require parity
receipts at phase gates. The sm-govt-nz route table also leaves x_twitter and
website/browser-fallback routes without parity evidence. Hansard (#183) is the
closest reference playbook.

## Core requirements
1. Pin the exact donor repository SHA at assimilation start; record it in track metadata and requirements.
2. Each assimilation phase gate requires a source-class parity receipt (donor vs canonical output on a fixed sample).
3. Close the two missing sm-govt-nz parity classes as part of this track or explicitly defer with rationale.
4. Source-rights classification for hathi-nz content must be preserved verbatim through the parity comparison.
