# Additional A2 tests

Student: Khoi Ngoc Minh Hoang.

These are student-authored tests, not the inaccessible instructor A2 grader.
Use the RISC-V GCC/QEMU toolchain, Python 3, pexpect, and a host C compiler.
No test-only kernel hooks or public syscall/ABI changes are introduced.

```
python3 -m pip install pexpect
python3 tests/run_all.py
python3 tests/test_qemu_mutations.py
```

`run_all.py` stops on the first failure and runs, in order:

1. Host policy harness using actual yield, sleep, mlfq_tick and mlfq_boost;
   five intentionally broken variants must be rejected.
2. Host orphan-reclamation harness using actual reap_orphans. Checks wait_lock
   before a single process lock, reclaiming only adopted zombies, preserving
   direct init children and other parents' children, and leaving live adopted
   children alone. Three intentionally broken variants must be rejected.
3. `usertests reparent`, CPUS=3, 20 consecutive runs per boot, three boots
   (60 runs). Keeping one guest alive exposes the accumulation missed by
   fresh-boot-only checks. Original usertests code is not modified.
4. `forktest`, CPUS=3, three consecutive runs. Ordinary resource exhaustion
   must still fail gracefully, and the parent must reap all its own children.
5. `a2policy`, CPUS=1, three boots. Checks partial sleep budgets, two complete
   level-3 proc-table round-robin rounds, and preemption on a higher-priority
   child's wake tick. Uses only public syscalls, pipes and getpinfo.
6. `a2check behavior`, CPUS=1. Checks ABI, bounds/copyout, counters, child
   reset, exact slice boundaries/dispatch counts, boost and process churn.
7. `a2check`, CPUS=3. Checks counters, bad arguments and concurrent churn.
8. `usertests -q`, CPUS=3, three fresh boots. Full xv6 quick regression suite.

The host mocks do not simulate SMP. Deterministic policy tests require CPUS=1;
CPUS=3 tests assert correctness rather than a fixed execution order.

To reproduce the specific reparent stability check:

```
python3 tests/run_qemu.py --cpus 3 --command 'usertests reparent' --runs-per-boot 20 --repeat 3
```

The runner checks each command's success marker AND return to the shell. A
panic, silent failure, or SOME TESTS FAILED cannot count as PASS. Failed runs
raise an error with their log path. Full logs go to ignored tests/logs/.
Deliberate user traps in usertests are expected only if the suite finishes
with ALL TESTS PASSED.

## Regression sensitivity

`test_qemu_mutations.py` builds four deliberately broken variants in separate
throwaway copies with fresh filesystems. a2policy must reject erased sleep
budget, disabled preemption and disabled round robin. On CPUS=3, repeated
original usertests reparent must reject disabled orphan reclamation. A mutant
is successful evidence only when it fails for the registered reason; mutant
code is never part of the submitted kernel.

Retained guest-output excerpts in tests/evidence/ separate passing runs from
expected mutant failures. See VERIFICATION.md for the version and run counts.
These finite checks do not replace official pinfotest, make grade, missing
A2 starter ancestry/header verification, or hidden concurrent stress tests.
