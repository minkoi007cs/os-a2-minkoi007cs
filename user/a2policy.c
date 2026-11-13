// Khoi Ngoc Minh Hoang - additional black-box MLFQ tests (CPUS=1 only).
// No testing syscalls or kernel scheduling hooks are added.
#include "kernel/types.h"
#include "kernel/pinfo.h"
#include "user/user.h"

static struct pinfo rows[64];
static void fail(char *s) { fprintf(2, "A2POLICY FAIL: %s\n", s); exit(1); }
static struct pinfo info(int pid) {
  int n=getpinfo(rows,64);
  if(n<0) fail("getpinfo");
  for(int i=0;i<n;i++) if(rows[i].pid==pid) return rows[i];
  fail("missing process");
  return rows[0];
}
static void reap(int n) {
  for(int i=0;i<n;i++) { int s; if(wait(&s)<0 || s) fail("child failed"); }
}
static void window(void) {
  while(uptime()%64<3 || uptime()%64>6) pause(1);
}
static void send(int fd, void *p, int n) {
  if(write(fd,p,n)!=n) fail("write");
}
static void receive(int fd, void *p, int n) {
  char *b=p;
  while(n) { int k=read(fd,b,n); if(k<=0) fail("short read"); b+=k; n-=k; }
}

static void sleep_budget(void) {
  window();
  int pid=fork(); if(pid<0) fail("fork");
  if(pid==0) {
    int slept=0;
    for(;;) {
      struct pinfo p=info(getpid());
      int expected=p.runticks<1?0:p.runticks<3?1:p.runticks<7?2:3;
      if(p.level!=expected) fail("sleep erased consumed budget");
      if(!slept && p.runticks==4) {
        if(p.level!=2) fail("sleep setup");
        int t=uptime();
        pause(2);
        struct pinfo after=info(getpid());
        if(uptime()-t<2) fail("did not actually sleep");
        if(after.level!=2 || after.runticks!=4) fail("sleep changed level/runtime");
        slept=1;
      }
      if(p.runticks>=8) break;
    }
    if(!slept) fail("missed sleep boundary");
    exit(0);
  }
  reap(1);
  printf("A2POLICY PASS: sleep preserves partial time slice\n");
}

// Each child logs only its first execution in a new level-3 dispatch.
// All records fit in the pipe without a reader, so logging never blocks.
struct record { int pid; int runticks; int nsched; };
static void round_robin(void) {
  window();
  int out[2],gate[2],ready[2],pids[3];
  if(pipe(out)<0 || pipe(gate)<0 || pipe(ready)<0) fail("pipe");
  for(int i=0;i<3;i++) {
    int pid=fork(); if(pid<0) fail("fork");
    if(pid==0) {
      close(out[0]); close(gate[1]); close(ready[0]);
      char c='r'; send(ready[1],&c,1); receive(gate[0],&c,1);
      close(gate[0]); close(ready[1]);
      int last=-1,logged=0;
      for(;;) {
        struct pinfo p=info(getpid());
        if(p.level==3 && p.nsched!=last) {
          struct record r={p.pid,p.runticks,p.nsched};
          send(out[1],&r,sizeof(r)); last=p.nsched; logged++;
        }
        if(p.runticks>=16) break;
      }
      if(logged!=2) fail("RR dispatch count / boost interference");
      close(out[1]); exit(0);
    }
    pids[i]=pid;
  }
  close(out[1]); close(gate[0]); close(ready[1]);
  char c[3]; receive(ready[0],c,3); close(ready[0]);
  // Derive the expected order from proc[] order, not PID allocation order.
  int ordered[3],count=0,n=getpinfo(rows,64);
  for(int i=0;i<n;i++)
    for(int j=0;j<3;j++) if(rows[i].pid==pids[j]) ordered[count++]=pids[j];
  if(count!=3) fail("RR process table");
  send(gate[1],"xxx",3); close(gate[1]);
  reap(3);
  struct record r[6]; receive(out[0],r,sizeof(r));
  if(read(out[0],c,1)!=0) fail("extra RR records");
  close(out[0]);
  int start=-1;
  for(int i=0;i<3;i++) if(ordered[i]==r[0].pid) start=i;
  if(start<0) fail("RR unknown pid");
  for(int i=0;i<6;i++) {
    if(r[i].pid!=ordered[(start+i)%3]) fail("proc-table round robin order");
    int expected=i<3?7:15;
    if(r[i].runticks!=expected) fail("RR slice duration");
  }
  printf("A2POLICY PASS: proc-table round robin, two complete level-3 rounds\n");
}

struct wake_record { int target; int actual; int parentlevel; int parentticks; };
static void preemption(void) {
  window();
  int ready[2],out[2]; if(pipe(ready)<0 || pipe(out)<0) fail("pipe");
  int parent=getpid(),pid=fork(); if(pid<0) fail("fork");
  if(pid==0) {
    close(ready[0]); close(out[0]);
    int target=uptime()+18;
    send(ready[1],&target,sizeof(target)); close(ready[1]);
    while(uptime()<target) pause(target-uptime());
    struct pinfo p=info(parent);
    struct wake_record r={target,uptime(),p.level,p.runticks};
    send(out[1],&r,sizeof(r)); close(out[1]); exit(0);
  }
  close(ready[1]); close(out[1]);
  int target; receive(ready[0],&target,sizeof(target)); close(ready[0]);
  while(uptime()<target+8) { }
  struct wake_record r; receive(out[0],&r,sizeof(r)); close(out[0]); reap(1);
  if(r.actual!=r.target) fail("higher-priority wakeup waited for slice end");
  if(r.parentlevel!=3 || r.parentticks<15 || r.parentticks>=23)
    fail("preemption setup did not interrupt a partial level-3 slice");
  printf("A2POLICY PASS: higher-priority wakeup preempts on its wake tick\n");
}

int main(void) {
  sleep_budget();
  round_robin();
  preemption();
  printf("A2POLICY ALL TESTS PASSED (CPUS=1)\n");
  exit(0);
}
