#include "kernel/types.h"
#include "kernel/stat.h"
#include "kernel/pinfo.h"
#include "user/user.h"

static struct pinfo rows[64];
static void fail(char *s) { fprintf(2, "A2CHECK FAIL: %s\n", s); exit(1); }
static struct pinfo self(void) {
  int n = getpinfo(rows, 64), pid = getpid();
  if(n < 1 || n > 64) fail("count");
  for(int i=0;i<n;i++) {
    if(rows[i].pid == pid) return rows[i];
  }
  fail("self missing");
  return rows[0];
}
int main(int argc, char **argv) {
  if(sizeof(struct pinfo) != 40) fail("ABI size");
  if(getpinfo(rows,-1) != -1 || getpinfo(0,0) != 0) fail("bounds");
  if(getpinfo((struct pinfo *)~(uint64)0,1) != -1) fail("bad pointer");
  if(getpinfo(rows,1) != 1) fail("max");
  struct pinfo initial = self();
  int t=uptime();
  while(uptime()-t < 20) { }
  struct pinfo after=self();
  if(after.runticks-initial.runticks < 15) fail("runtime accounting");
  if(after.nsched <= initial.nsched) fail("dispatch accounting");
  if(after.ctime != initial.ctime) fail("creation time changed");
  int fds[2]; if(pipe(fds)<0) fail("pipe");
  int child=fork();
  if(child<0) fail("fork");
  if(child==0) {
    close(fds[0]);
    struct pinfo p=self();
    if(p.runticks > 2 || p.nsched > 3 || p.level > 1) fail("inherited counters");
    write(fds[1],"x",1); close(fds[1]); exit(0);
  }
  close(fds[1]); char c; if(read(fds[0],&c,1)!=1) fail("child check");
  close(fds[0]); int st; if(wait(&st)!=child || st) fail("child status");
  if(argc>1) {
    // Start a fresh child away from a boost, with its parent blocked in wait.
    while(uptime()%64 < 5 || uptime()%64 > 10) pause(1);
    child=fork();
    if(child<0) fail("slice fork");
    if(child==0) {
      for(;;) {
        struct pinfo p=self();
        int r=p.runticks;
        int level = r<1 ? 0 : r<3 ? 1 : r<7 ? 2 : 3;
        int dispatches = 1+(r>=1)+(r>=3)+(r>=7);
        if(r>=15) dispatches += (r-7)/8;
        if(p.level != level) fail("slice boundary");
        if(p.nsched != dispatches) fail("unnecessary tick yield");
        if(r>=17) break;
      }
      exit(0);
    }
    if(wait(&st)!=child || st) fail("slice child");
    // One-CPU behavioral check: reach level 3, then observe the 64-tick boost.
    while(uptime()%64 > 3) pause(1);
    t=uptime();
    int saw3=0, boosted=0;
    while(uptime()-t < 70) {
      struct pinfo p=self();
      if(p.level==3) saw3=1;
      if(saw3 && p.level<=1) boosted=1;
    }
    if(!saw3 || !boosted) fail("demotion/boost");
  }
  for(int round=0;round<4;round++) {
    for(int j=0;j<12;j++) {
      int pid=fork(); if(pid<0) fail("stress fork");
      if(pid==0) {
        for(int k=0;k<4;k++) {
          self(); pause(1);
          volatile int x=0; for(int n=0;n<60000;n++) x+=n;
          (void)x;
        }
        exit(0);
      }
    }
    for(int j=0;j<12;j++) if(wait(&st)<0 || st) fail("stress wait");
  }
  printf("A2CHECK PASS: ABI, copyout, counters, fork reset, scheduling, stress\n");
  exit(0);
}
