# Requirements

- **MCP-1** Implement the stable MCP 2025-11-25 initialize lifecycle and require
  `protocolVersion`, `capabilities`, and `clientInfo`.
- **MCP-2** Do not serve tools or resources before the initialized notification.
- **MCP-3** Emit no response for notifications and reject request-shaped
  lifecycle notifications.
- **MCP-4** Validate list cursors and tool arguments fail closed.
- **MCP-5** Return unknown tools and malformed calls as JSON-RPC invalid params;
  return known-tool domain failures as tool results with `isError: true`.
- **MCP-6** Return missing resources as MCP resource-not-found error `-32002`.
- **MCP-7** Declare JSON Schema 2020-12 input and output schemas, and keep text
  content semantically identical to `structuredContent`.
- **MCP-8** Inspect the real sharded CAS layout and verify object fixity by
  streaming through `ContentAddressedStore`; never call an empty store healthy.
- **MCP-9** Preserve the read-only archive product boundary. Do not add search,
  mutation, publication, rights, or cutover tools.
- **MCP-10** Keep all publication, redistribution, workflow, live execution,
  recovery, cutover, and donor-archive gates pending.

