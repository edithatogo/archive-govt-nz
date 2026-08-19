# Plan: Weekly Orchestration, Monthly Reconciliation, and Recovery Drills

1. **Phase 1: Workflow Specification and State Machine Binding**
   - Bind cron schedules and environment secrets to weekly, monthly, and quarterly workflows.
2. **Phase 2: Recovery Harness & Fixity Verification**
   - Implement bitstream recovery and fixity assertions in `src/archive_govt_nz/recovery_harness.py`.
3. **Phase 3: Automated Assurance**
   - Verify workflow schemas and execution logic through the test suite.
