#!/usr/bin/env python3

import os
import sys
import json
import glob
import subprocess


C_GREEN = '\033[92m'
C_RED   = '\033[91m'
C_RESET = '\033[0m'


with open('asmtest.json') as f:
    config = json.loads(f.read())

test_path = config['test_path'] if 'test_path' in config else 'test'

if 'init' in config:
    for init_cmd in config['init']:
        subprocess.run(init_cmd)

working_dir = '.asmtest'

os.makedirs(working_dir, exist_ok=True)

rendered_asm = os.path.join(working_dir, 'test.asm')
rendered_bin = os.path.join(working_dir, 'test.a')

tests_total = 0
tests_successful = 0


def run_suite(suite_name):
    global tests_total
    global tests_successful

    with open(os.path.join(test_path, suite_name + '.asmtest')) as f:
        raw = f.read().split('-----')
        template = raw[0]
        suite = json.loads(raw[1])

    for case in suite['cases']:
        rendered = template

        for k,v in case.items():
            if not k.startswith('expect_'):
                rendered = rendered.replace('{{ ' + k + ' }}', v)

        with open(rendered_asm, 'w') as f:
            f.write(rendered)

        if 'before_each' in config:
            for before_each_cmd in config['before_each']:
                subprocess.run(before_each_cmd, shell=True)

        res = subprocess.run([rendered_bin], stdout=subprocess.PIPE)

        messages = []

        def expect_check(name, expected, actual):
            if expected != actual:
                messages.append('Expected {} [{}] but found [{}].'.format(
                                name, expected, actual))


        if 'expect_status' in case:
            expect_check('status', int(case['expect_status']), res.returncode)

        stdout = res.stdout.strip().decode('utf-8')

        if 'expect_stdout' in case:
            expect_check('stdout', case['expect_stdout'],
                         res.stdout.strip().decode('utf-8'))

        if not len(messages):
            status = C_GREEN + 'PASS' + C_RESET
            tests_successful += 1
        else:
            status = C_RED + 'FAIL' + C_RESET

        print('[{}] {}: {}'.format(status, suite_name, case['name']))

        for message in messages:
            print('  {}'.format(message))

        tests_total += 1


if len(sys.argv) >= 2:
    # Only suites on command line
    suite_names = sys.argv[1:]
else:
    # All suites
    suite_names = [
        f[len(test_path) + 1 : -len('.asmtest')] for f in
        glob.glob(os.path.join(test_path, '**', '*.asmtest'), recursive=True)
    ]

for suite_name in suite_names:
    run_suite(suite_name)

if tests_total == tests_successful:
    print("\n{}/{} tests successful.".format(tests_successful, tests_total))
