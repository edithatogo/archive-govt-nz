# Windows integration repair

Hosted Windows run 34081970376 (job 101618835479) exposed inherited capture
failures plus normalization test portability problems: fsync on a read-only
WARC handle raised EBADF, question-mark filenames could not be created, and
the oversized CSV parameter expanded PYTEST_CURRENT_TEST beyond Windows' limit.
The initial log wrapper stopped before complete failure details; direct job-log
readback established the causes. No unrelated authentication was changed.

The capture runner now opens its newly written owned WARC in non-truncating
read/write mode solely for fsync. A red regression modeled the writable-handle
requirement and failed before the change; it now passes and verifies the same
WARC digest. No flush failure is suppressed and no fsync is removed.

Donor parity's synthetic filename uses space, hash and percent characters that
are valid on all supported platforms while still exercising literal-path
handling. Population oversized-input fixtures are unchanged; short explicit
parameter IDs avoid exporting the payload as a test identifier.

Eighty focused checkpoint/process-recovery/population/oracle tests pass locally.
This is not a native Windows success receipt. Full integration and corrected
hosted Windows checks remain required; patch coverage is tracked separately.
