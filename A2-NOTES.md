# A2: CPU scheduling

Implements syscall 23 `getpinfo(struct pinfo *, int)` and four-level MLFQ:
1, 2, 4, 8 tick slices, per-level proc-table round robin, no forgiveness on
sleep/voluntary yield, higher-level preemption, global boost every 64 ticks.

## Starter provenance - unresolved before submission

On 2026-11-12 the PDF's URL, https://github.com/guanslab/xv6-a2-starter,
returned "Repository not found". The instructor's public repositories listed
`xv6-a1-starter` but no A2 starter. This working copy starts from the pristine
instructor A1 starter commit `cf3305a` (no student A1 modifications), preserving
its history. `kernel/pinfo.h` was transcribed from the A2 PDF with exactly the
specified field order and a 40-byte layout.

This is a provisional implementation. The official A2 starter, its header and
public tests must be compared before submission. Its missing commit history
cannot be manufactured. No claim is made that the official A2 public or hidden
tests passed. No `make grade` target is fabricated.

## Build and test

Use a RISC-V GCC toolchain and QEMU 7.2 or later:

```
make CPUS=1 qemu
# xv6 shell:
a2check behavior
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
