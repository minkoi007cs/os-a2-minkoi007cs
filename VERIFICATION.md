# Verification (2026-11-13, America/New_York)

The reparent fix was tested with RISC-V GCC 16.2.0 and QEMU 11.1.2.
Kernel and filesystem were rebuilt from source in an isolated clean copy.
Source equality with the working tree was checked; SHA-256 values for all
82 source/build/test files are in tests/evidence/reparent-fix/SOURCE_SHA256.json.
The 60 reparent runs used the same kernel source in the working build.

| Check | Result |
| --- | --- |
| RISC-V kernel and filesystem build | PASS |
| Original usertests reparent, CPUS=3 | 60/60 PASS: 20 consecutive commands per boot, 3 fresh boots |
| forktest, CPUS=3 | 3/3 consecutive runs PASS |
| a2policy, CPUS=1 | 3/3 fresh boots PASS |
| a2check behavior, CPUS=1 | PASS: exact slices/dispatches, boost, ABI, counters, child reset, copyout, churn |
| a2check, CPUS=3 | PASS |
| Full usertests -q, CPUS=3 | 3/3 fresh boots: ALL TESTS PASSED |
| Host policy harness | PASS; all 5 broken variants rejected |
| Host orphan-reclamation harness | PASS; all 3 broken variants rejected |
| QEMU mutations in isolated copies | All 4 rejected for registered failure reasons |
| git diff --check | PASS |

## Regression and fix

The original a2-submit commit a766ad6 intermittently failed reparent, including
when the original usertests reparent was repeated in one guest. An isolated
diagnostic copy showed proc[] full (64 entries), init RUNNABLE at level 1,
and most remaining entries level-0 zombies. Strict priority let fresh forks
outpace init's orphan reaping before the next boost.

On allocation failure, kfork now reclaims only adopted ZOMBIE children of
init under wait_lock -> p->lock and retries allocation once after progress.
Direct children of init and children of other parents remain waitable; live
adopted children are not freed. The scheduler's specified MLFQ rules and
original usertests are unchanged. See A2-NOTES.md for lock/lifetime details.
The old statement that no concrete kernel defect existed is superseded.

The QEMU no_orphan_reclamation mutant disables the new fallback. Repeated
original usertests reparent then produces SOME TESTS FAILED, as required by
the mutation runner. This complements the 60 passing repaired-kernel runs;
the regression test would not silently accept the original missing fallback.

## Evidence and reproduction

Current logs are in tests/evidence/reparent-fix/. before-reparent.log records
the original PASS then FAIL. before-diagnostic.log is explicitly from an
isolated diagnostic copy with extra printing, not submitted usertests.
mutant-* logs are EXPECTED FAILURES of temporary broken copies. Other logs
show passing runs. The 3cpu-usertests_reparent-* logs contain all 60 passes.
Older evidence in tests/evidence/ belongs to the pre-fix November 12 audit;
it is historical, not the basis for current stability claims.

```
python3 tests/run_all.py
python3 tests/test_qemu_mutations.py
```

Requires Python pexpect, a host C compiler, RISC-V GCC and QEMU. See tests/
README.md. These finite checks do not enumerate all SMP interleavings.
Official pinfotest, make grade and hidden tests remain unavailable. The A2
starter ancestry and original header are unverified; no score is asserted.

Canvas confirmed submission of the repository URL on November 13 at 10:37pm
(America/New_York). See SUBMISSION.md for the receipt and grading-tag policy.
