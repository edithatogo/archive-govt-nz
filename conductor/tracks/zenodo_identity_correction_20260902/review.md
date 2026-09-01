# Review

Self-review found and resolved two critical publication-state defects: the legacy adapter fabricated a DOI and published status without a remote operation, and the client checked DOI confirmation only after the irreversible publish request. The adapter is now preparation-only; a credential cannot produce a false success. The client requires explicit release approval, canonical reserved DOI confirmation, exact draft identity/state before POST, and independent exact published readback afterward.

Current registries, contracts, generator output, and documentation now distinguish concept `20592539` from version `20592540`. A tracked-file semantic regression test rejects new false labels while explicitly allowing named immutable historical evidence and the additive correction receipt.

No Hugging Face card or merge-state contract changed. No external Zenodo write occurred. A future meaningful release must use the typed template and stop at explicit publication approval.
