# Additional A2 tests

Student: Khoi Ngoc Minh Hoang.

These are student-authored tests, not the missing instructor A2 public grader.
No kernel test hooks, new syscalls, or production ABI changes are required.
Use the same RISC-V GCC and QEMU toolchain as the kernel. Host policy tests
also require `cc`; the QEMU runner requires Python 3 and `pexpect`.

```
python3 -m pip install pexpect
python3 tests/run_all.py
python3 tests/test_qemu_mutations.py
```

`run_all.py` fails on the first failing step. It runs:

1. Host unit harness: extracts and compiles the actual `yield`, `sleep`,
   `mlfq_tick`, and `mlfq_boost` functions from kernel/proc.c. Checked mocks
   verify preservation of every partial slice on voluntary yield, both sleep
   paths, demotion after preserved time, higher-priority preemption without
   forgiving time, no preemption for sleeping/same-priority peers, boost of
   all live states, and no nested process locks on those tested paths.
   This single-CPU mock cannot establish real interrupt or SMP correctness.
2. `a2policy`, CPUS=1, three fresh boots: black-box guest tests using only
   existing public syscalls. Actual sleep preserves partial time; three
   processes execute two complete round-robin rounds at level 3 in proc[]
   order; a sleeping level-0 child wakes while its level-3 parent is partway
   through a slice and must run on the wake tick. Tests synchronize with
   pipes and select windows away from the 64-tick boost. Logs fit in the pipe
   without blocking, and the parent waits while the round-robin trace runs.
3. `a2check behavior`, CPUS=1: ABI, copyout, counters, fork reset, exact slice
   boundaries/dispatch counts, boost, and fork/sleep/exit stress.
4. `a2check`, CPUS=3: counters, invalid arguments and concurrent stress.
5. `usertests -q`, CPUS=3: full xv6 quick regression suite.

The deterministic `a2policy` test must run with CPUS=1. It does not claim a
fixed process execution order under CPUS=3.

## Regression sensitivity

The host harness also compiles five intentionally wrong variants in temporary
files and requires each to fail: resetting budget in yield, resetting it in
sleep, disabling higher-level preemption, resetting budget during preemption,
and yielding on every tick. It never edits the working kernel.

`test_qemu_mutations.py` copies the project into separate temporary directories,
rebuilds each variant from source with a fresh filesystem, and proves that the
guest policy test rejects sleep-budget reset, disabled higher-priority
preemption, and selection from the beginning of proc[] instead of round robin.
The original source, normal build and Git history are untouched. These wrong
variants are test inputs only and must never be submitted as the solution.

Full run logs are written to ignored `tests/logs/`. Guest-output excerpts
from the verified run are preserved in `tests/evidence/`; mutant excerpts
are expected failures and are labeled separately. The QEMU runner requires both a
return to the shell and the appropriate success marker; a silent guest failure
or panic cannot count as PASS. Deliberate bad-address traps inside usertests
are normal if that suite ultimately prints ALL TESTS PASSED.

## Limits

These tests improve coverage of the PDF requirements, but do not enumerate all
concurrent interleavings and do not replace the official starter's header,
commit history, pinfotest, make grade, or hidden stress tests. See AUDIT.md.
