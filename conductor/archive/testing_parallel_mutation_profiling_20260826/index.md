# Track: Testing Modernization: Pytest-Gremlins Mutation, Parallel xdist, Property-Based Hypothesis & Scalene Profiling

## Overview
This track expands test assurance across `archive-govt-nz`:
1. **Mutation testing**: configure `pytest-gremlins` for coverage-guided
   in-memory mutation switching alongside the targeted AST mutation runners.
2. **Test parallelisation**: evaluate `pytest-xdist` loadscope process
   isolation and record comparable timing evidence.
3. **Property-based testing**: add Hypothesis coverage for canonical URNs,
   multihash fixity, Arrow serialization, and Aho-Corasick matchers.
4. **Resource profiling**: add bounded Scalene CPU, native-memory, and copy
   overhead profiling with machine-readable receipts.

## Specification & Plan
- [Specification](./spec.md)
- [Requirements](./requirements.md)
- [Design](./design.md)
- [Implementation Plan](./plan.md)
- [Run Log](./runlog.md)
- [Evidence](./evidence.md)
- [Review](./review.md)
