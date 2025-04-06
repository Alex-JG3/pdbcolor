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

PDB Color also has tab autocompletion by default which can be triggered using
the TAB key. For example:

```python
$ python3 main.py
> /home/alex/documents/pdbcolor/main.py(9)<module>()
-> y = 2
(Pdb) str.
str.capitalize(    str.isalpha(       str.ljust(         str.rpartition(
str.casefold(      str.isascii(       str.lower(         str.rsplit(
str.center(        str.isdecimal(     str.lstrip(        str.rstrip(
str.count(         str.isdigit(       str.maketrans(     str.split(
str.encode(        str.isidentifier(  str.mro()          str.splitlines(
str.endswith(      str.islower(       str.partition(     str.startswith(
str.expandtabs(    str.isnumeric(     str.removeprefix(  str.strip(
str.find(          str.isprintable(   str.removesuffix(  str.swapcase(
str.format(        str.isspace(       str.replace(       str.title(
str.format_map(    str.istitle(       str.rfind(         str.translate(
str.index(         str.isupper(       str.rindex(        str.upper(
str.isalnum(       str.join(          str.rjust(         str.zfill(
(Pdb) str.
```

## Examples

Using PDB:

![Code example using PDB](images/before.png)

Using PDB Color:

![Code example using PDB](images/after.png)
