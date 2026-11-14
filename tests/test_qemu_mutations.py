#!/usr/bin/env python3
"""Ensure black-box policy tests reject known regressions in isolated copies.

Production files, git history, and the normal build remain untouched.
Requires pexpect, RISC-V GCC and QEMU. Each mutant gets a fresh filesystem.
"""
from pathlib import Path
import shutil
import tempfile
import pexpect

ROOT=Path(__file__).resolve().parents[1]
mutations=[
    ('sleep_forgets', 'kernel/proc.c', '    p->state = SLEEPING;',
     '    p->usedticks = 0;\n    p->state = SLEEPING;',
     'A2POLICY FAIL: sleep erased consumed budget', 'a2policy', 1),
    ('no_preemption', 'kernel/proc.c', '    if (higher)\n      return 1;',
     '    if (higher && 0)\n      return 1;',
     'A2POLICY FAIL: higher-priority wakeup waited for slice end', 'a2policy', 1),
    ('no_round_robin', 'kernel/proc.c', '      int start = cursor[level];',
     '      int start = (cursor[level] * 0 + NPROC - 1);',
     'A2POLICY FAIL: proc-table round robin order', 'a2policy', 1),
    ('no_orphan_reclamation', 'kernel/proc.c',
     'if (np == 0 && reap_orphans() > 0)',
     'if (np == 0 && (0 && reap_orphans() > 0))',
     'SOME TESTS FAILED', 'usertests reparent', 20),
]
for name,file,old,new,expected,command,runs in mutations:
    with tempfile.TemporaryDirectory(prefix='xv6-mutant-') as tmp:
        dest=Path(tmp)
        shutil.copytree(ROOT,dest,dirs_exist_ok=True,ignore=shutil.ignore_patterns(
            '.git','*.o','*.d','*.asm','*.sym','*.img','_*','logs','__pycache__'))
        # Non-underscore build binaries also need to be rebuilt from sources.
        for artifact in ('kernel/kernel','mkfs/mkfs','user/usys.S'):
            (dest/artifact).unlink(missing_ok=True)
        source=dest/file
        text=source.read_text()
        assert old in text, name
        source.write_text(text.replace(old,new,1))
        log_path=ROOT/'tests/logs'/f'mutant-{name}.log'
        log_path.parent.mkdir(exist_ok=True)
        with log_path.open('w') as log:
            cpus = 3 if command == 'usertests reparent' else 1
            child=pexpect.spawn('make',[f'CPUS={cpus}','qemu'],cwd=str(dest),encoding='utf-8',timeout=180)
            child.logfile_read=log
            try:
                child.expect_exact('$ ')
                for _ in range(runs):
                    child.sendline(command)
                    child.expect_exact('$ ')
                    output=child.before
                    if expected in output:
                        break
                    assert 'ALL TESTS PASSED' in output, output[-3000:]
                assert expected in output, f'{name}: unexpected result; see {log_path}\n{output[-3000:]}'
                assert 'A2POLICY ALL TESTS PASSED' not in output, name
                child.send('\x01x');child.expect(pexpect.EOF)
            finally:
                child.close(force=True)
        print(f'MUTATION REJECTED {name}: {expected}',flush=True)
