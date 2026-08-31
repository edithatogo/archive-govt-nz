# Project Workflow

## Guiding principles

1. The plan is the source of truth for tracked work.
2. The tech stack is deliberate. Document stack changes before implementation.
3. Prefer test-driven development for code changes.
4. Keep outputs deterministic and rerunnable.
5. Preserve provenance and auditability for corpus artifacts.
6. Prefer non-interactive commands and CI-compatible execution.

## Standard task workflow

1. Select the next task from the active plan or track.
2. Mark it in progress before making changes.
3. Write or update tests that define the expected behavior.
4. Run the relevant test command and confirm the failure mode before fixing.
5. Implement the smallest change needed to make tests pass.
6. Refactor only after the green state is restored.
7. Run the relevant validation checks for the change.
8. Update documentation when behavior, interfaces, or operational steps change.
9. Commit related changes together with a clear message.

## Validation expectations

- Run `pytest` for Python behavior changes.
- Run `ruff` for formatting and lint checks when code changes are made.
- Run `ty check` when type-sensitive code changes are made.
- Prefer narrow, task-specific validation over broad unrelated sweeps.
- Mock or isolate networked services in tests unless the task explicitly
  requires live verification.

## External service workflow

- Treat Hugging Face, Zenodo, and the NZ Legislation API as external systems.
- Use environment variables or explicit credentials for live operations.
- Do not assume remote state without checking the live response or generated
  artifact.
- Keep destructive or publishing operations separate from local validation.

## Documentation workflow

- Update `README.md`, `docs/`, or track notes when the user-facing contract
  changes.
- Keep setup, usage, and release instructions aligned with the actual CLI and
  scripts.
- Record deviations from the documented stack before or alongside code changes.

## Quality gates

- Tests pass.
- Linting passes.
- Types are sound for the touched surface.
- Outputs remain deterministic.
- Documentation matches the implemented behavior.
