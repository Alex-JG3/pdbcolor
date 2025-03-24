# PDB Color

Add some color to the python debugger.

## Installation and Setup

Can be installed with `pip`.

```
pip install pdbcolor
```

Once installed, set the environment variable `PYTHONBREAKPOINT` to
`pdbcolor.set_trace`. This can be done with the `export` command with a POSIX
compliant shell.

```
export PYTHONBREAKPOINT=pdbcolor.set_trace
```

`pdbcolor` can be used temporarily by adding the
`PYTHONBREAKPOINT=pdbcolor.set_trace` prefix before running a python script.
For example:

```
PYTHONBREAKPOINT=pdbcolor.set_trace python3 main.py
```
