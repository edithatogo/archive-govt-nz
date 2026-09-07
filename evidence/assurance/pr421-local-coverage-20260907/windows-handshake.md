# Windows subprocess handshake correction

PR #421 at `71f7fe8f` passed Linux, macOS and the patch coverage check,
but Windows job `101622027259` in run `34083113498` reported one failure,
5,540 passing tests and two skips. The sole failure compared the child process
text output `checkpoint_ready\r\n` with the expected binary handshake
`checkpoint_ready\n`. Coverage remained above the required threshold (97.78%).

Commit `7b672a9c7448ec4ffb5f925553b70761db2f3993` makes the synthetic child
write and flush the exact bytes through `sys.stdout.buffer`. It does not change
production code or weaken the checkpoint, hard-kill, lock ownership, WARC
fixity or resume assertions. The focused process-recovery test passed locally;
an independent review reproduced that pass and found no issues.

Native Windows confirmation is pending the corrected hosted run. A successful
local test is not recorded as Windows success. PR #422 inherits this correction
at `3c446166`; the source-contract integration inherits it at `dc5ba26a`.

Source: <https://github.com/edithatogo/archive-govt-nz/actions/runs/34083113498/job/101622027259>.
