#!/usr/bin/env python3
"""Check actual orphan reclamation against a lock-checking host mock.

QEMU reparent/forktest exercise the real lifecycle and SMP paths separately.
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'kernel/proc.c').read_text()
match = re.search(r'static int\nreap_orphans\(void\)\n\{', source)
assert match
end = match.end()
depth = 1
while depth:
    depth += (source[end] == '{') - (source[end] == '}')
    end += 1
body = source[match.start():end]

prelude = r'''
#include <assert.h>
#include <stdio.h>
#define NPROC 8
enum { UNUSED, USED, SLEEPING, RUNNABLE, RUNNING, ZOMBIE };
struct spinlock { int held; };
struct proc {
  struct spinlock lock;
  struct proc *parent;
  int orphaned, state;
};
static struct proc proc[NPROC];
static struct proc *initproc = &proc[0];
static struct spinlock wait_lock;
static int process_locks, freed;
static void acquire(struct spinlock *lock) {
  assert(!lock->held);
  if (lock == &wait_lock) assert(process_locks == 0);
  else { assert(wait_lock.held); assert(++process_locks == 1); }
  lock->held = 1;
}
static void release(struct spinlock *lock) {
  assert(lock->held);
  if (lock == &wait_lock) assert(process_locks == 0);
  else assert(--process_locks == 0);
  lock->held = 0;
}
static void freeproc(struct proc *p) {
  assert(wait_lock.held && p->lock.held && process_locks == 1);
  assert(p->state == ZOMBIE && p->parent == 0 && p->orphaned == 0);
  p->state = UNUSED;
  freed++;
}
'''
main = r'''
int main(void) {
  // Adopted zombies are reclaimable. Direct init children, live parents'
  // zombies, and adopted children still running/sleeping must survive.
  proc[0].state = RUNNABLE;
  proc[1] = (struct proc){.parent=initproc,.orphaned=1,.state=ZOMBIE};
  proc[2] = (struct proc){.parent=initproc,.orphaned=0,.state=ZOMBIE};
  proc[3] = (struct proc){.parent=&proc[2],.orphaned=0,.state=ZOMBIE};
  proc[4] = (struct proc){.parent=initproc,.orphaned=1,.state=RUNNING};
  proc[5] = (struct proc){.parent=initproc,.orphaned=1,.state=SLEEPING};
  proc[6] = (struct proc){.parent=initproc,.orphaned=1,.state=RUNNABLE};
  proc[7] = (struct proc){.parent=initproc,.orphaned=1,.state=ZOMBIE};
  assert(reap_orphans() == 2 && freed == 2);
  assert(proc[1].state == UNUSED && proc[7].state == UNUSED);
  assert(proc[2].state == ZOMBIE && proc[2].parent == initproc);
  assert(proc[3].state == ZOMBIE && proc[3].parent == &proc[2]);
  assert(proc[4].state == RUNNING && proc[5].state == SLEEPING);
  assert(proc[6].state == RUNNABLE);
  assert(reap_orphans() == 0 && freed == 2);
  assert(process_locks == 0 && !wait_lock.held);
  for (int i=0; i<NPROC; i++) assert(!proc[i].lock.held);
  puts("ORPHAN UNIT PASS: adopted zombies only, wait ownership, lock order");
}
'''

with tempfile.TemporaryDirectory(prefix='xv6-orphan-unit-') as tmp:
    directory = Path(tmp)
    for label, function, should_pass in [
        ('actual', body, True),
        ('steal_init_child', body.replace(' || !p->orphaned', ''), False),
        ('free_live_child', body.replace('p->state == ZOMBIE', 'p->state != UNUSED'), False),
        ('skip_reclamation', body.replace('      reaped++;', '      reaped += 0;'), False),
    ]:
        cfile = directory / f'{label}.c'
        binary = directory / label
        cfile.write_text(prelude + function + main)
        subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                        str(cfile), '-o', str(binary)], check=True)
        result = subprocess.run([str(binary)], capture_output=True, text=True)
        assert (result.returncode == 0) == should_pass, label + result.stderr
        print(result.stdout.strip() if should_pass else 'MUTATION REJECTED: ' + label)
