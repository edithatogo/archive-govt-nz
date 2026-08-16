# Track 1 Requirements (MoSCoW)

## Must Have
- **MUST-1**: Record exact donor commit SHA (`24df5f2dea7cfcd85fecaa1a18845339f987eeec`) and target commit SHA (`b1c09da305822f3e8f85f1c4e7a85eb803565ec2`).
- **MUST-2**: Inventory all 66 donor GitHub Actions workflows and identify their cron schedules.
- **MUST-3**: Record all secret/variable names without exposing secret values.
- **MUST-4**: Inventory existing external publication IDs on Hugging Face and Zenodo.

## Should Have
- **SHOULD-1**: Create deterministic baseline fixtures of donor raw captures.
- **SHOULD-2**: Map all package identities and entry point commands.

## Could Have
- **COULD-1**: Generate automated baseline diff report comparing file inventories.

## Won't Have
- **WONT-1**: No modification of remote Hugging Face datasets, Zenodo depositions, or GitHub repositories in this track.
