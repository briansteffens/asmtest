#!/usr/bin/env python3

import os
import sys
import json
import glob
import subprocess
from subprocess import Popen, call, PIPE
import shutil


def shell_call(cmd):
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    output, err = p.communicate()
    return (p.returncode, output, err)


term_width, _ = shutil.get_terminal_size((80, 20))


C_GREEN = '\033[92m'
C_RED   = '\033[91m'
C_BOLD  = '\033[97m'
C_GRAY  = '\033[90m'
C_RESET = '\033[0m'


with open('asmtest.json') as f:
    config = json.loads(f.read())

test_path = config['test_path'] if 'test_path' in config else 'test'

if 'init' in config:
    for init_cmd in config['init']:
        subprocess.call(init_cmd, shell=True)

working_dir = '.asmtest'

os.makedirs(working_dir, exist_ok=True)

rendered_asm_fn = config['rendered_file'] if 'rendered_file' in config \
                                          else 'test.asm'

rendered_asm = os.path.join(working_dir, rendered_asm_fn)
rendered_bin = os.path.join(working_dir, 'test.a')

tests_total = 0
tests_successful = 0


def print_pass_fail(case_name, passed):
    global tests_successful

    out_line = '    ' + case_name

    if len(out_line) > term_width - 7:
        out_line = out_line[:term_width - 7]

    while len(out_line) < term_width - 6:
        out_line = out_line + ' '

    if passed:
        status = C_GREEN + 'PASS' + C_RESET
        tests_successful += 1
    else:
        status = C_RED + 'FAIL' + C_RESET

    print(out_line + '[' + status + ']')


def run_suite(suite_name):
    global tests_total
    global tests_successful

    with open(os.path.join(test_path, suite_name + '.asmtest')) as f:
        raw = f.read().split('-----')
        template = raw[0]
        suite = json.loads(raw[1])

    first = True

    print(C_BOLD + suite_name + C_RESET)

    for case in suite['cases']:
        tests_total += 1
        rendered = template

        for k,v in case.items():
            if not k.startswith('expect_'):
                rendered = rendered.replace('{{ ' + k + ' }}', v)

        with open(rendered_asm, 'w') as f:
            f.write(rendered)

        nextCase = False

        if 'before_each' in config:
            for before_each_cmd in config['before_each']:
                res, _, _ = shell_call(before_each_cmd)
                if res != 0:
                    print_pass_fail(case['name'], False)
                    print('{}Error running before_each script for test '
                          '{}.{}: {}{}'.format(C_GRAY, suite_name,
                          case['name'], before_each_cmd, C_RESET))
                    nextCase = True
                    break

        if nextCase:
            continue

        cmd = config['run']
        if 'args' in case:
            cmd += ' ' + case['args']
        res, stdout, _ = shell_call(cmd)

        messages = []

        def expect_check(name, expected, actual):
            if expected != actual:
                messages.append('Expected {} [{}] but found [{}].'.format(
                                name, expected, actual))


        if 'expect_status' in case:
            expect_check('status', int(case['expect_status']), res)

        stdout = stdout.strip().decode('utf-8')

        if 'expect_stdout' in case:
            expect_check('stdout', case['expect_stdout'], stdout)

        print_pass_fail(case['name'], len(messages) == 0)

        for message in messages:
            print('  {}'.format(message))

        first = False


if len(sys.argv) >= 2:
    # Only suites on command line
    suite_names = sys.argv[1:]
else:
    # All suites
    files = glob.glob(os.path.join(test_path, '*.asmtest'))
    files.sort()
    suite_names = [f[len(test_path) + 1 : -len('.asmtest')] for f in files]

for suite_name in suite_names:
    run_suite(suite_name)

print("\n{}/{} tests successful.".format(tests_successful, tests_total))
