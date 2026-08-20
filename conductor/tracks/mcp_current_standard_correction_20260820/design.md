# Design

The stdio process remains dependency-light and line-delimited. A stateful
JSON-RPC dispatcher enforces `new -> initializing -> ready`. Static tool
descriptors carry Draft 2020-12 schemas; `jsonschema` validates arguments.
One-page list methods accept only an absent or null cursor. The archive status
tool discovers canonical sharded SHA-256 objects and streams verification.

Protocol and domain errors remain distinct: malformed requests use JSON-RPC
errors, while failures executing a known, valid tool use MCP tool error results.

