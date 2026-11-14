# A2: CPU scheduling

Student: **Khoi Ngoc Minh Hoang**
Course: Fall 2026 OPERATING SYSTEMS (CS-33211-001)
GitHub: `minkoi007cs`

Implements syscall 23 `getpinfo(struct pinfo *, int)` and four-level MLFQ:
1, 2, 4, 8 tick slices, per-level proc-table round robin, no forgiveness on
sleep/voluntary yield, higher-level preemption, global boost every 64 ticks.

## Starter provenance - still unresolved

On 2026-11-12 the PDF's URL, https://github.com/guanslab/xv6-a2-starter,
returned "Repository not found". The instructor's public repositories listed
`xv6-a1-starter` but no A2 starter. This working copy starts from the pristine
instructor A1 starter commit `cf3305a` (no student A1 modifications), preserving
its history. `kernel/pinfo.h` was transcribed from the A2 PDF with exactly the
specified field order and a 40-byte layout.

This is a provisional implementation. The official A2 starter, its header and
public tests still need to be obtained and compared. Its missing commit history
cannot be manufactured. No claim is made that the official A2 public or hidden
tests passed. No `make grade` target is fabricated.

## Build and test

Use a RISC-V GCC toolchain and QEMU 7.2 or later. The reproducible additional
student regression suite is documented in tests/README.md:

```
python3 tests/run_all.py
python3 tests/test_qemu_mutations.py
```

For manual guest checks:

```
make CPUS=1 qemu
# xv6 shell:
a2check behavior
a2policy
# Quit with Ctrl-A, X. Restart:
make CPUS=3 qemu
# xv6 shell:
a2check
usertests -q
```

`a2check` is an additional student-side test, not the instructor's public test.
It covers struct size, max limits, negative max, failed copyout, tick and dispatch
accounting, stable creation time, fresh child counters and repeated concurrent
fork/sleep/exit workloads. The optional `behavior` mode checks exact slice boundaries and dispatch counts, and observes demotion
to level 3 and a subsequent boost on one CPU.

Lock order: `run_lock -> p->lock` for scheduler selection; release run_lock
before context switching. The tick scanner holds at most one process lock.
The boost uses `tickslock -> p->lock`. getpinfo snapshots each process under
its lock, then releases it before copyout. allocproc reads ticks without taking
tickslock to avoid reversing that order.

## Reparent regression and orphan reclamation (2026-11-13)

Repeated `usertests reparent` on CPUS=3 exposed process-table exhaustion.
Diagnostics in an isolated copy showed all 64 slots occupied, init RUNNABLE
at level 1, and most other entries ZOMBIE at level 0. Fresh level-0 forks
could defer init long enough that it could not reap adopted children before
the next fork needed a slot. The old assertion that all tests always pass
was incorrect: the original kernel passed some runs and failed others.

The fix marks children adopted after their original parent exits. If process
allocation fails, kfork reclaims only adopted ZOMBIE children of init under
wait_lock -> p->lock, then retries allocation once if anything was reclaimed.
The original parent is gone and init discards these exit statuses. Init's
own children, including its shell, and all children of other live parents
remain available to wait(). The process lock prevents freeing a zombie that
has not finished switching away from its kernel stack. Exhaustion without
reclaimable orphans still returns -1; fork does not wait indefinitely.

The four MLFQ levels, time slices, round-robin cursors, no-forgiveness rule,
64-tick boost, getpinfo ABI, and the original usertests are unchanged.
`orphaned` is internal kernel state protected by wait_lock and is reset when
assigning a new child's parent and when removing a reaped child.

The regression runner now supports repeated commands in one boot. Fresh boots
alone missed the accumulation that exposed the original failure. See tests/README.md and VERIFICATION.md for the exact validation and its limits.
