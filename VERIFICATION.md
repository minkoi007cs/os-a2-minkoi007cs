# Verification (2026-11-12, America/New_York)

- RISC-V GCC/QEMU build: PASS.
- `a2check behavior`, CPUS=1: PASS, including exact 1/2/4/8 tick slice
  boundaries and dispatch counts (no unnecessary tick yields), boost,
  statistics, copyout failures, bounds, child reset, fork/sleep/exit stress.
- `a2check`, CPUS=3: PASS.
- `usertests -q`, CPUS=3, final kernel: ALL TESTS PASSED.
- `git diff --check`: PASS.

The custom a2check program is not the official pinfotest/public grader.
The official A2 starter and tests are unavailable; see A2-NOTES.md. These
results cannot establish a grading score or validate the missing A2 ancestry.

The unmodified instructor starter remains the root commit; no submitted A1
solution was used. No Canvas submission has been made.
