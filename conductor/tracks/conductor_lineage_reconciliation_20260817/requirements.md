# Track 2 Requirements (MoSCoW)

## Must Have
- **MUST-1**: Inventory all 39 donor tracks with their original identifiers, titles, and statuses.
- **MUST-2**: Assign exactly one disposition to every donor track (`historical_import`, `mapped_to_target_track`, `superseded`, `duplicate`, `deferred`, or `rejected_with_reason`).
- **MUST-3**: Establish immutable historical import destination path (`conductor/archive/imported/sm-govt-nz/<SHA>/`).

## Should Have
- **SHOULD-1**: Create a cross-reference map between donor track IDs and target consolidation tracks.

## Won't Have
- **WONT-1**: Do not reopen completed historical donor tracks as active target tracks unless new integration verification is required.
