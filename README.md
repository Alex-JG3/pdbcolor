# PDB Color

Add some color to the python debugger.

## Installation

Install with `pip`.

```shell
pip install pdbcolor
```

## Setup

Python can be configured to use PDB Color by changing the `PYTHONBREAKPOINT`
environment variable. To use PDB Color temporarily, add the 
`PYTHONBREAKPOINT=pdbcolor.set_trace` prefix before running your python script:

```shell
PYTHONBREAKPOINT=pdbcolor.set_trace python3 main.py
```

To make PDB Color the default for all Python sessions, set the
`PYTHONBREAKPOINT` environment variable to `pdbcolor.set_trace`. On Mac and
Linux, you can do this with the `export` command:

```shell
export PYTHONBREAKPOINT=pdbcolor.set_trace
```

Add this line to your terminal configuration file (e.g. `.bashrc` or `.zshrc`)
to ensure the setting persists across terminal settings.

## Usage

PDB Color is a drop-in replacement for PDB that simply adds color to PDB's
outputs. See the [PDB documentation](https://docs.python.org/3/library/pdb.html)
for a PDB introduction.

## Examples

Using PDB:

![Code example using PDB](images/before.png)

Using PDB Color:

![Code example using PDB](images/after.png)
