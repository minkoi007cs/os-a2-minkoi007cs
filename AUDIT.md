# Acceptance audit - OS Assignment 2

Student: **Khoi Ngoc Minh Hoang**
GitHub: `minkoi007cs`
Updated: 2026-11-13, America/New_York

## Findings

1. **Fixed: reparent failures under MLFQ process-table pressure.** Fresh review
   disproved the previous claim that no kernel defect existed. The original
   a2-submit commit a766ad6 intermittently failed usertests -q on CPUS=3 and
   repeated usertests reparent in one boot. An isolated diagnostic run showed
   64 occupied slots, init RUNNABLE at level 1, and mostly level-0 zombies.
   Fresh high-priority forks could prevent init from reaping orphans in time.
   kfork now reclaims adopted zombies on allocation failure and retries once.
   wait_lock protects adoption/ownership; one p->lock at a time protects
   state and reclamation after the process switches away. Direct children of
   init and children of live parents are not reclaimed by this helper. The
   MLFQ selection and accounting rules and original usertests are unchanged.
   Validation details and evidence are in VERIFICATION.md.
2. **Open: official A2 starter, ancestry and grader.** The official URL still
   returned 404 on November 13. This repo starts at pristine A1 starter
   cf3305a, not student A1 work. The PDF requires A2 starter history and its
   unchanged supplied header. The transcribed pinfo.h has the correct PDF
   layout but cannot be compared with the unavailable file. pinfotest and
   make grade have not been run. Obtain the official starter and compare/port
   this work and run its tests before claiming full compliance or a score.
3. **Resolved: submission status and identity.** The repo is public with the
   required name and identifies Khoi Ngoc Minh Hoang. Canvas confirmed the
   repository URL submission on November 13 at 10:37pm. Earlier claims that
   Canvas access was blocked or no submission existed are superseded. The
   student authorized updating the tested source and grading tag.

## Requirement trace

| PDF requirement | Evidence / remaining limit |
| --- | --- |
| A2 starter history and unchanged supplied pinfo.h | OPEN: official source unavailable; PDF layout matches |
| Syscall 23; exact user getpinfo prototype | syscall.h/c, sysproc.c, user.h, usys.pl; runtime ABI checks |
| runticks in both trap paths; nsched per dispatch; ctime at creation | proc.c/trap.c; counters, child reset and stable creation-time tests |
| proc[] order, skip UNUSED, max/error semantics | getpinfo; bounds and copyout tests |
| Snapshot with p lock, copyout after unlock | getpinfo code and invalid-pointer tests |
| Highest-priority level, per-level proc[] round robin | scheduler; a2policy trace |
| Four levels, 1/2/4/8 ticks, demote/reset at exhaustion | mlfq_tick; exact slice/dispatch tests |
| Sleep/yield/preemption preserve partial time | host harness and a2policy |
| Global CPU-0 boost every 64 ticks | clockintr/mlfq_boost; behavior test |
| Correct under CPUS=3 process churn and usertests -q | Reparent fix; repeated reparent, forktest and full quick suites |
| Public repo, main, a2-submit, Canvas URL submission | SUBMISSION.md; GitHub refs are checked after push |

The available checks do not enumerate all concurrent interleavings, replace
hidden stress tests, or establish 100/100. See VERIFICATION.md for actual run
counts and tests/evidence for retained logs.
