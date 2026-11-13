# Verification (2026-11-12, America/New_York)

- RISC-V GCC/QEMU build: PASS.
- `a2check behavior`, CPUS=1: PASS, including exact 1/2/4/8 tick slice
  boundaries and dispatch counts (no unnecessary tick yields), boost,
  statistics, copyout failures, bounds, child reset, fork/sleep/exit stress.
- `a2check`, CPUS=3: PASS.
- `usertests -q`, CPUS=3, final kernel: ALL TESTS PASSED.
- `a2policy`, CPUS=1: PASS on three fresh boots, including two complete
  proc-table round-robin rounds, sleep with a partially consumed slice, and
  higher-priority wakeup preemption on the wake tick.
- Host policy harness using actual kernel function bodies: PASS; voluntary
  yield preserves all partial slices, sleep/preemption preserve budgets,
  demotion and boost update the right fields, checked process locks balance.
- Host mutation checks: all five intentionally broken variants rejected.
- QEMU mutation checks in isolated copies: sleep reset, disabled preemption,
  and disabled round robin all rejected for the intended reason.
- `git diff --check`: PASS.

Guest-output excerpts are preserved in `tests/evidence/` (including explicitly
labeled, expected failures for the three isolated mutants).

Reproduce with `python3 tests/run_all.py` and
`python3 tests/test_qemu_mutations.py`; see tests/README.md for scope.
The production kernel is unchanged from the audited implementation; the new
tests did not expose a concrete kernel defect requiring a code fix.

The custom a2check program is not the official pinfotest/public grader.
The official A2 starter and tests are unavailable; see A2-NOTES.md. These
results cannot establish a grading score or validate the missing A2 ancestry.

The unmodified instructor starter remains the root commit; no submitted A1
solution was used. No Canvas submission has been made.
