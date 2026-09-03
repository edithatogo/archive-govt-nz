# Recovery boundary

```mermaid
flowchart TD
  A[Reviewed authority revision and rights] --> B{Package available?}
  B -->|No| C[Blocked preflight receipt]
  B -->|Yes| D[Fresh isolated retrieval]
  D --> E[Outer and inner verification]
  E --> F[Restore and reconcile]
  F --> G[No-write parent authority check]
  G --> H[Independent second retrieval and restore]
```

No publication client or package-format changes. Every failed branch retains evidence outside the disposable workspace. No retained Actions artifact or local package substitution.
