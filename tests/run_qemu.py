#!/usr/bin/env python3
"""Checked QEMU runner. Requires Python pexpect and the usual xv6 toolchain."""
from pathlib import Path
import argparse
import re
import pexpect

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--cpus', type=int, choices=(1, 3), required=True)
parser.add_argument('--command', required=True)
parser.add_argument('--repeat', type=int, default=1)
parser.add_argument('--log-dir', type=Path, default=ROOT / 'tests' / 'logs')
parser.add_argument('--timeout', type=int, default=900)
args = parser.parse_args()
if args.command in ('a2policy', 'a2check behavior') and args.cpus != 1:
    parser.error('deterministic policy assertions require CPUS=1')
if args.repeat < 1:
    parser.error('repeat must be positive')
expected = {
    'a2policy': 'A2POLICY ALL TESTS PASSED (CPUS=1)',
    'a2check': 'A2CHECK PASS:',
    'a2check behavior': 'A2CHECK PASS:',
    'usertests -q': 'ALL TESTS PASSED',
}
if args.command not in expected:
    parser.error('command has no registered success marker')
args.log_dir.mkdir(parents=True, exist_ok=True)
for i in range(1, args.repeat + 1):
    log_path = args.log_dir / f'{args.cpus}cpu-{args.command.replace(" ", "_")}-{i}.log'
    with log_path.open('w') as log:
        child = pexpect.spawn('make', [f'CPUS={args.cpus}', 'qemu'],
                              cwd=str(ROOT), encoding='utf-8', timeout=args.timeout)
        child.logfile_read = log
        try:
            child.expect_exact('$ ')
            child.sendline(args.command)
            child.expect_exact('$ ')
            output = child.before
            if expected[args.command] not in output or re.search(
                    r'(?:A2\w* FAIL:|\bpanic:|SOME TESTS FAILED)', output):
                raise RuntimeError(f'guest did not pass; see {log_path}\n{output[-3000:]}')
            child.send('\x01x')
            child.expect(pexpect.EOF)
        finally:
            child.close(force=True)
    print(f'PASS {args.cpus} CPU {args.command} run {i}/{args.repeat}: {log_path}', flush=True)
