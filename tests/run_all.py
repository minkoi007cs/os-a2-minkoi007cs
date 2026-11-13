#!/usr/bin/env python3
"""Run the additional student test suite; this is not the official make grade."""
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
for args in [
    ['tests/test_policy_unit.py'],
    ['tests/run_qemu.py','--cpus','1','--command','a2policy','--repeat','3'],
    ['tests/run_qemu.py','--cpus','1','--command','a2check behavior'],
    ['tests/run_qemu.py','--cpus','3','--command','a2check'],
    ['tests/run_qemu.py','--cpus','3','--command','usertests -q'],
]:
    subprocess.run([sys.executable,*args],cwd=ROOT,check=True)
print('STUDENT REGRESSION SUITE PASSED',flush=True)
