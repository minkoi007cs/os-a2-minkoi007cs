# Acceptance audit - OS Assignment 2

Student: **Khoi Ngoc Minh Hoang** (name displayed by Canvas)
GitHub: `minkoi007cs`
Audit date: 2026-11-12, America/New_York

## Decision: provisional implementation; submission acceptance is BLOCKED

No definite kernel implementation defect was found in this review. The code
implements the behavior described by the PDF and the available runtime checks
pass. This is not proof of a score, exhaustive correctness, or equivalence to
the missing official A2 starter.

### Open findings

1. **High priority: official starter provenance and grader unavailable.** The
   PDF requires a fresh `guanslab/xv6-a2-starter` with its original pinfo.h,
   public pinfotest and make grade. That repository still returns HTTP 404 to
   the authenticated GitHub account. This copy instead preserves the pristine
   instructor A1 starter history; it does not contain any student A1 solution.
   The A2 header has been transcribed from the PDF. Its field order and size
   match the PDF, but the original A2 header and ancestry cannot be verified.
   Required resolution: obtain the instructor's accessible A2 starter, port
   the changes onto its actual history without editing its supplied header,
   and run its public grader. Custom tests cannot replace that requirement.
2. **Submission steps pending by design:** `main` is public under the required
   repository name, but `a2-submit` is absent and no repository link has been
   submitted to Canvas. The user requested review before submission. Tagging
   and Canvas submission remain final actions after review and resolution of
   finding 1.
3. **Identity omission - fixed:** the first draft had only the GitHub username
   in commit metadata, not the student's full name in the project documents.
   README and A2-NOTES.md now identify Khoi Ngoc Minh Hoang. No student number
   was invented; the PDF does not request one. Original xv6 credits remain.

## Requirement trace

| PDF requirement | Implementation evidence | Verification / status |
| --- | --- | --- |
| A2 starter and full history; supplied header unchanged | See finding 1 | BLOCKED |
| getpinfo syscall 23 and exact user prototype | kernel/syscall.h, syscall.c, sysproc.c; user/user.h, usys.pl | Code review + runtime call |
| pinfo pid/state/level/runticks/nsched/ctime/name[16] in that order | kernel/pinfo.h | PDF layout + 40-byte runtime assertion; official file pending |
| Timer charge in both user and kernel trap paths under p lock | trap.c -> mlfq_tick in proc.c | Code review + spin/syscall workload |
| nsched increments on each dispatch | scheduler | Exact one-CPU dispatch checks |
| ctime set in allocproc without tickslock | allocproc | Code review + stable-ctime check |
| New processes/children reset counters, level and time used | allocproc; kfork calls allocproc and does not overwrite fields | Fresh-child and slice tests |
| getpinfo skips UNUSED, proc[] order, stops at max | getpinfo proc-table loop | Code review; runtime count/max checks |
| Negative max/copy failure return -1; max=0 returns 0 | getpinfo | Runtime negative max, bad pointer and zero max |
| Snapshot under p lock, copyout after unlocking | getpinfo | Lock review + failed-copyout test |
| Four priorities, level 0 highest | scheduler loops 0 through 3 | Code review |
| proc[] round robin using one cursor per level | cursor[4], run_lock, scheduler | Code review; no dedicated full ordering trace test |
| Time slices 1/2/4/8, bottom remains 3 | mlfq_tick | Exact one-CPU boundaries and dispatch-count checks |
| Sleep/voluntary yield retain level and used time | sleep/yield do not reset either field | Code review; no dedicated early-yield boundary test |
| Preempt for a higher-level RUNNABLE process; otherwise keep running | mlfq_tick scans after releasing own lock | Code review; no dedicated wakeup/preemption trace test |
| Boost every 64 global ticks on CPU 0 | clockintr -> mlfq_boost | Code review + observed boost test |
| One process lock at a time; no scheduler selection lock over swtch | scheduler, mlfq_tick, mlfq_boost, getpinfo | Lock review + 3-CPU stress and usertests |
| Public repository with required name and main | minkoi007cs/os-a2-minkoi007cs | Remote checked |
| Push a2-submit tag; submit link on Canvas | Not done | Pending final approval; see finding 2 |

## Available test evidence

- RISC-V GCC/QEMU build succeeds.
- `a2check behavior`, CPUS=1: PASS (rechecked during audit).
- `a2check`, CPUS=3: PASS.
- `usertests -q`, CPUS=3 on the unchanged kernel: ALL TESTS PASSED.
- `git diff --check`: clean.

The runtime checks cover useful behavior but do not exhaust every interleaving
or the instructor's hidden tests. Round-robin ordering, early-yield budget
retention, and higher-priority wakeup preemption were reviewed in source;
there are no dedicated dynamic trace tests for those three properties yet.
