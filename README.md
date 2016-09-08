asmtest
=======

A script to help with unit testing assembly code.

![Console output example](https://s3.amazonaws.com/briansteffens/asmtest.png)

# Overview

The basic idea is I wanted to be able to write unit tests for functions written
in assembly, but ran into a few annoyances:

1. It takes quite a bit of boilerplate to write a little test program to call
   an assembly language function, which gets out of hand if you want a lot of
   very similar test cases (the same code with slightly different inputs and
   expected outputs).
2. Verifying the expected output of a function can be a little rough. Numeric
   values are fine but if you want to compare strings you have to write or
   bring in a string comparison function.
3. You could write the tests in a higher level language like C, but then the
   high level language has to conform to the same calling conventions used by
   the assembly code under test. This is not always a problem but it could get
   messy if you wanted to test internal assembly functions or functions meant
   to be called by a different language or platform.

The solution I came up with is a simple little python script and related
config files that use templating to generate slightly different versions of
the same testing code, assemble and link to the code under test, then run the
resulting binary and validate the output (either status code or stdout).

A standard setup will look like this:

## Project config file

A file called `asmtest.json` should be created in the root of the project
directory:

```json
{
    "init": [
        "make"
    ],
    "before_each": [
        "nasm -f elf64 .asmtest/test.asm -o .asmtest/test.o",
        "ld .asmtest/test.o bin/libbasm.a -o .asmtest/test.a"
    ]
}
```

`init` and `before_each` are arrays of shell commands to be executed:

- `init` defines commands to be run at the beginning of the test script, prior
  to any tests.
- `before_each` lists the shell commands to be run before each test suite
  (`*.asmtest` files). These commands are responsible for generating an
  executable test program.

## Test files

Test suite files are located (by default) in the directory `test/`. *Note: this
can be customized by setting the `test_path` to something else in
`asmtest.json`.* Each test file defines a code template and a list of cases.
Here's an example, located at `test/str_cmp.asmtest`:

```asm
extern str_cmp

section .data

    left  db "{{ left }}", 0
    right db "{{ right }}", 0

section .text
global _start
_start:
    mov rdi, left
    mov rsi, right
    call str_cmp
    mov rdi, rax

    mov rax, 60
    syscall

-----

{
    "cases": [
        {
            "name": "Match, same length",
            "left": "Greetings!",
            "right": "Greetings!",
            "expect_status": 1
        },
        {
            "name": "No match, same length",
            "left": "Greetings!",
            "right": "Greetings?",
            "expect_status": 0
        }
    ]
}
```

An `.asmtest` file has two components, separated by 5 dashes (`-----`):

1. The template code. This will be rendered out with replacements made for
   each test case.
2. The JSON section, which defines the test cases to use the template code.

## Running through the example

So we've got a config file located at `./asmtest.json` and a test located at
`./test/str_cmp.asmtest`. We could now run the test in two different ways. To
run only a named test:

```bash
asmtest str_cmp
```

To run all tests in the `./test/` path:

```bash
asmtest
```

When `asmtest` runs, the following will happen:

1. The `init` commands in `asmtest.json` will be run, in this case causing the
   project under test to be rebuilt.
2. The first case template will be generated. "Greetings!" will be substituted
   for `{{ left }}` and `{{ right }}` in the template code. This rendered
   template code will be written to `.asmtest/test.asm`.
3. The `before_each` commands will run. In this case, this will assemble the
   rendered template `.asmtest/test.asm`, then link that with the code under
   test, producing an executable at `.asmtest/test.a`.
4. The executable at `.asmtest/test.a` will be executed. Its return code will
   be compared to the `expect_status` value of the first case. If they match,
   this test case will be considered a pass. If not, it will be marked as a
   failure.
5. The second case template will be generated. "Greetings!" will be substituted
   for `{{ left }}` and "Greetings?" will be substituted for `{{ right }}` in
   the template.
6. The `before_each` commands will run, assembling and linking this new
   rendered template.
7. The executable will be run and its exit status code will be compared to the
   `expect_status` value of the second case.
8. A report of both cases and whether they passed or failed will be printed to
   the console.

In the above example, `make` is run before any tests. This can be any command
you want, but the idea is to have it rebuild the project being tested. This
can perform any other necessary setup as well.

Next, before each test suite (`*.asmtest` file), the `before_each` shell
commands are run. Again, these are pretty flexible, but `before_each` commands
are mostly responsible for converting `.asmtest/test.asm` (the rendered test
template) into an executable `.asmtest/test.a` file. The reason these commands
are configurable is to allow you to use whichever assembler or platform you
want and link to whatever other modules you want.

# Downloading and installing

You need git and python3. Then:

```bash
git clone https://github.com/briansteffens/asmtest
cd asmtest
sudo make install
```

To uninstall:

```bash
sudo make uninstall
```

# The asmtest.json config file

This file can contain the following settings:

- **init**: a list of shell commands to be executed before any test suites are
  run.
- **before_each**: a list of shell commands to be executed before each test
  suite file is run. These commands must convert the rendered template at
  `./.asmtest/test.asm` to an executable at `./.asmtest/test.a`.
- **test_path** *(Optional)*: Customizes the default location of test suite
  files. By default this is `./test`.

# Test cases

Each test case in a `*.asmtest` file can contain the following:

- **expect_status**: The expected exit status code. The test fails if this
  doesn't match the status code of `./.asmtest/test.a`.
- **expect_stdout**: The expected terminal output. The test fails if this
  doesn't match the actual console output of `./.asmtest/test.a`.

In addition, any number of **template replacements** can be found in a case.
The values of any unrecognized keys will replace `{{ key }}` in the code
template. This allows the same template to be reused for many different similar
test cases.

# More examples

A more real-life example of asmtest in use can be found at
<https://github.com/briansteffens/libbasm>.
