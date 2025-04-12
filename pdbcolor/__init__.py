import linecache
import re
import rlcompleter
import sys
from pdb import Pdb

from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.formatters.terminal import TERMINAL_COLORS
from pygments.lexer import RegexLexer
from pygments.lexers import PythonLexer
from pygments.token import Comment, Generic, Name


class PdbColor(Pdb):
    _colors = {
        "black": 30,
        "red": 31,
        "green": 32,
        "yellow": 33,
        "blue": 34,
        "purple": 35,
        "cyan": 36,
        "white": 37,
        "Black": 40,
        "Red": 41,
        "Green": 42,
        "Yellow": 43,
        "Blue": 44,
        "Purple": 45,
        "Cyan": 46,
        "White": 47,
        "bold": 1,
        "light": 2,
        "blink": 5,
        "invert": 7,
    }

    def __init__(
        self,
        completekey="tab",
        stdin=None,
        stdout=None,
        skip=None,
        nosigint=False,
        readrc=True,
    ):
        super().__init__(completekey, stdin, stdout, skip, nosigint, readrc)
        self.colors = TERMINAL_COLORS.copy()
        self.colors[Comment] = ("green", "brightgreen")

        self.lexer = PythonLexer()
        self.path_lexer = PathLexer()
        self.formatter = TerminalFormatter(colorscheme=self.colors)

        self.prompt = self._highlight("(Pdb) ", "purple")
        self.breakpoint_char = self._highlight("B", "purple")
        self.currentline_char = self._highlight("->", "purple")
        self.prompt_char = self._highlight(">>", "purple")
        self.line_prefix = self._highlight("->", "purple")
        self._return = self._highlight("--Return--", "green")
        self.path_prefix = self._highlight(">", "purple") + " "
        self.eof = self._highlight("[EOF]", "green")
        self.tag = ":TAG:"

    def _highlight(self, text: str, color: str) -> str:
        return f"\x1b[{self._colors[color]}m" + text + "\x1b[0m"

    # Autocomplete
    complete = rlcompleter.Completer(locals()).complete

    def highlight_code(self, lines: list[str]) -> list[str]:
        """Highlight code and 'tag' to end of each line for easy identification.

        Parameters
        ----------
        lines: list[str]
            Lines of python code.

        Returns
        -------
        list[str]
            Highlighted lines of code.
        """
        # Find the index of the first non-whitespace character
        first = 0
        for i, line in enumerate(lines):
            if not line.isspace():
                first = i
                break

        # Find the index of the last non-whitespace character
        last = len(lines)
        for i in range(len(lines) - 1, 0, -1):
            if not lines[i].isspace():
                last = i
                break

        # Pygment's highlight function strips newlines at the start and end.
        # These lines are important so we add them back in later
        highlighted: str = highlight(
            "".join(lines[first : last + 1]), self.lexer, self.formatter
        ).splitlines(keepends=True)

        # Add tag to the end of each line to allow code lines to be more easily
        # identified
        highlighted = [line + self.tag for line in highlighted]

        return lines[:first] + highlighted + lines[last + 1 :]

    def _print_lines(self, lines: list[str], start: int, breaks=(), frame=None):
        """Print a range of lines.

        Parameters
        ----------
        lines: list[str]
            List of lines to print.
        start: int
            The line number of the first line in 'lines'
        """
        if len(lines) == 0:
            super()._print_lines(lines, start, breaks, frame)
            return

        # Highlight all lines to improve the highlighting accuracy. Highlighting
        # just a few lines can lead to mistakes
        filename = self.curframe.f_code.co_filename
        all_lines = linecache.getlines(filename, self.curframe.f_globals)
        highlighted = self.highlight_code(all_lines)

        # Line numbers start at 0 or 1 depending on the python version. The
        # following helps to ensure line number begins at 1.
        if lines[0] == all_lines[start]:
            # The lines numbers start at 0, force then to start at 1
            super()._print_lines(
                highlighted[start : start + len(lines)], start + 1, breaks, frame
            )
        else:
            # The lines numbers start at 1
            super()._print_lines(
                highlighted[start - 1 : start + len(lines)], start, breaks, frame
            )

    def message(self, msg: str):
        """Highlight and print message to stdout."""
        if msg.endswith(self.tag):
            # Check if 'msg' is a line of code
            msg = self.highlight_line_numbers_and_pdb_chars(msg.rstrip(self.tag))
        elif msg[0] == ">":
            # 'msg' contains the current line and path
            path, current_line = msg.split("\n")
            path = highlight(path[2:], self.path_lexer, self.formatter)
            msg = self.path_prefix + path + self.line_prefix + " " + current_line[3:]
        elif msg == "--Return--":
            msg = self._return
        elif msg == "[EOF]":
            msg = self.eof
        super().message(msg.rstrip())

    def highlight_line_numbers_and_pdb_chars(self, code_line: str) -> str:
        """Highlight line numbers and pdb characters in line of code.

        For example, in the following line ' 11  ->  for i in range(10):', The
        line number and current line character '->' will be highlighted.

        Parameters
        ----------
        code_line: str
            Line of code to be highlighted.

        Returns
        -------
        str
            Highlighted line.
        """
        line_number = re.search(r"\d+", code_line)
        if not line_number:
            return code_line

        start, end = line_number.span()
        line_number = self._highlight(code_line[start:end], "yellow")

        new_msg = code_line[:start] + line_number
        if code_line[end + 2 : end + 4] == "->":
            new_msg += " " + self.currentline_char + " " + code_line[end + 4 :]
        elif code_line[end + 2] == "B":
            new_msg += " " + self.breakpoint_char + "  " + code_line[end + 4 :]
        else:
            new_msg += code_line[end:]
        return new_msg


class PathLexer(RegexLexer):
    name = "Path"
    alias = ["path"]
    filenames = ["*"]

    tokens = {
        "root": [
            (r"[^/()]+", Name.Attribute),  # Match everything but '/'
            (r"->", Generic.Subheading),  # Match '/'
            (r"[/()<>]", Generic.Subheading),  # Match '/'
        ]
    }


def set_trace(frame=None):
    debugger = PdbColor()

    # The arguments here are copied from the PDB implementation of 'set_trace'
    debugger.set_trace(sys._getframe().f_back)
