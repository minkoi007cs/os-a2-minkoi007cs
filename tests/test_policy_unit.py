#!/usr/bin/env python3
"""Run actual kernel policy functions against a checked, single-CPU mock.

This complements QEMU tests; it does not model multiprocessor concurrency.
No production syscall/ABI or kernel testing hook is introduced. Function
bodies are extracted verbatim and compiled with the host C compiler.
"""
from pathlib import Path
import subprocess
import tempfile
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "kernel/proc.c").read_text()

def function(name):
    match = re.search(r"(?:int|void)\n" + name + r"\([^)]*\)\n\{", SOURCE)
    assert match, name
    start = match.start()
    pos = match.end()
    depth = 1
    while depth:
        depth += (SOURCE[pos] == "{") - (SOURCE[pos] == "}")
        pos += 1
    return SOURCE[start:pos]

PRELUDE = r'''
#include <assert.h>
#include <stdio.h>
#define NPROC 8
struct spinlock { int held; };
enum { UNUSED, USED, SLEEPING, RUNNABLE, RUNNING, ZOMBIE };
struct proc {
  struct spinlock lock;
  int state, level, usedticks, runticks, nsched, ctime;
  void *chan;
};
static struct proc proc[NPROC];
static int locks, switches;
static struct proc *myproc(void) { return &proc[0]; }
static void acquire(struct spinlock *l) {
  assert(!l->held); l->held=1; locks++;
  assert(locks==1); // Each tested path must hold at most one process lock.
}
static void release(struct spinlock *l) {
  assert(l->held); l->held=0; locks--;
}
static void sched(void) {
  assert(locks==1 && myproc()->lock.held);
  assert(myproc()->state!=RUNNING);
  switches++;
  myproc()->state=RUNNING;
}
'''
MAIN = r'''
static void reset(int level, int used) {
  assert(locks==0);
  for(int i=0;i<NPROC;i++) proc[i]=(struct proc){0};
  proc[0]=(struct proc){.state=RUNNING,.level=level,.usedticks=used,
                        .runticks=20,.nsched=9,.ctime=2};
  switches=0;
}
int main(void) {
  const int slices[]={1,2,4,8};
  for(int level=0;level<4;level++) {
    // Voluntary yield retains every partially consumed slice, including zero.
    for(int used=0;used<slices[level];used++) {
      reset(level,used);
      yield();
      assert(switches==1 && proc[0].level==level && proc[0].usedticks==used);
      assert(proc[0].runticks==20 && proc[0].nsched==9);
      int preempt=mlfq_tick(&proc[0]);
      assert(proc[0].runticks==21);
      assert(preempt==(used+1==slices[level]));
      assert(proc[0].usedticks==(preempt?0:used+1));
      assert(proc[0].level==(preempt && level<3?level+1:level));
    }
  }
  // Sleep both when truly sleeping and when a prior wakeup cleared chan.
  for(int waiting=0;waiting<2;waiting++) {
    reset(2,3); proc[0].chan=waiting?(void *)1:0;
    sleep();
    assert(switches==waiting && proc[0].level==2 && proc[0].usedticks==3);
    assert(proc[0].runticks==20);
    assert(mlfq_tick(&proc[0])==1);
    assert(proc[0].level==3 && proc[0].usedticks==0);
  }
  // Higher-priority RUNNABLE preempts without resetting the partial budget.
  for(int level=1;level<4;level++) {
    reset(level,0);
    proc[7]=(struct proc){.state=RUNNABLE,.level=level-1};
    assert(mlfq_tick(&proc[0])==1);
    assert(proc[0].level==level && proc[0].usedticks==1);
  }
  // Sleeping high-priority and runnable same/lower priority must not preempt.
  reset(3,1);
  proc[1]=(struct proc){.state=SLEEPING,.level=0};
  proc[2]=(struct proc){.state=RUNNABLE,.level=3};
  assert(mlfq_tick(&proc[0])==0 && proc[0].usedticks==2);
  // Boost all live states but do not reset lifetime statistics.
  for(int i=0;i<NPROC;i++)
    proc[i]=(struct proc){.state=i%6,.level=3,.usedticks=7,
                         .runticks=42,.nsched=11,.ctime=3};
  mlfq_boost();
  for(int i=0;i<NPROC;i++) {
    assert(proc[i].level==(proc[i].state==UNUSED?3:0));
    assert(proc[i].usedticks==(proc[i].state==UNUSED?7:0));
    assert(proc[i].runticks==42 && proc[i].nsched==11 && proc[i].ctime==3);
  }
  assert(locks==0);
  puts("POLICY UNIT PASS: voluntary yield, sleep, partial budgets, preemption, boost, locks");
}
'''

bodies = {name: function(name) for name in ("yield", "sleep", "mlfq_tick", "mlfq_boost")}

def run(directory, label, replacements=None):
    funcs = dict(bodies)
    for name, old, new in replacements or []:
        assert old in funcs[name]
        funcs[name] = funcs[name].replace(old, new, 1)
    code = PRELUDE + "\n".join(funcs.values()) + MAIN
    path = directory / (label + ".c")
    path.write_text(code)
    binary = directory / label
    subprocess.run(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", str(path), "-o", str(binary)], check=True)
    return subprocess.run([str(binary)], capture_output=True, text=True)

with tempfile.TemporaryDirectory(prefix="xv6-policy-") as tmp:
    directory = Path(tmp)
    result = run(directory, "actual")
    assert result.returncode == 0, result.stdout + result.stderr
    print(result.stdout.strip())
    # Prove these assertions reject the intended regressions, in throwaway C
    # harnesses only. No production source or build tree is mutated.
    mutations = [
        ("yield_forgets", [("yield", "p->state = RUNNABLE;", "p->usedticks = 0; p->state = RUNNABLE;")]),
        ("sleep_forgets", [("sleep", "p->state = SLEEPING;", "p->usedticks = 0; p->state = SLEEPING;")]),
        ("no_preemption", [("mlfq_tick", "if (higher)", "if (higher && 0)")]),
        ("preemption_forgets", [("mlfq_tick", "if (higher)\n      return 1;", "if (higher) { p->usedticks = 0; return 1; }")]),
        ("always_yield", [("mlfq_tick", "  return 0;", "  return 1;")]),
    ]
    for name, changes in mutations:
        result = run(directory, name, changes)
        assert result.returncode != 0, "test failed to reject " + name
        print("MUTATION REJECTED:", name)
