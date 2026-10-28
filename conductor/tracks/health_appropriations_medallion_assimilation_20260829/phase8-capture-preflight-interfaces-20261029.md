# Capture-plan operator preflight

The pinned preservation-only capture schedule now has a main CLI preflight and
read-only MCP tool. Both call the same packaged plan validation and source
selection as the existing scheduler; neither contacts sources or writes output.
The compact receipt reports pins and count, without source paths or URLs. Changed
plan/census pins fail closed. The existing explicit scheduler execution continues
to use the capture checkpoint, durable resume, and preservation-only rights.

Focused validation on Python 3.15.1 covers CLI/MCP parity, read-only behavior,
tamper rejection, existing execution and capture recovery contracts. This does
not expose capture execution through MCP, activate a schedule, assess rights,
or close the Phase 8 checkpoint. The full harness and hosted delivery are
separate gates.
