// Layout transcribed verbatim from the A2 PDF; compare with official starter.
#ifndef XV6_PINFO_H
#define XV6_PINFO_H
struct pinfo {
  int pid;
  int state;
  int level;
  int runticks;
  int nsched;
  int ctime;
  char name[16];
};
#endif
