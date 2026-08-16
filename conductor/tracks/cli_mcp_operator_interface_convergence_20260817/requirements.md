# Track 8 Requirements (MoSCoW)

## Must Have
- **MUST-1**: Implement canonical `archive-govt-nz` subcommands: `version`, `doctor`, `capabilities`, `sources`, `capture`, `archive`, `derivatives`, `search`, and `publish`.
- **MUST-2**: Provide `sm-govt-nz` and `nz-govt-social` entry points in `pyproject.toml` pointing to `src/archive_govt_nz/cli/compat.py`.
- **MUST-3**: Implement `--json` flag producing schema-validated JSON envelopes for all commands.
- **MUST-4**: Conform strictly to standard POSIX exit codes (0 to 5).

## Should Have
- **SHOULD-1**: Include automated CLI contract snapshot tests.

## Won't Have
- **WONT-1**: Do not implement an MCP server without demonstrated consumer demand.
