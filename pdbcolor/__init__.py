from pdb import Pdb
import sys
import re
import linecache
import reprlib
import string

from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.lexer import RegexLexer
from pygments.formatters import TerminalFormatter
from pygments.token import Generic, Comment, Name
from pygments.formatters.terminal import TERMINAL_COLORS


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

    def __init__(self):
        super().__init__()
        self.colors = TERMINAL_COLORS.copy()
        self.colors[Comment] = ("green", "brightgreen")

        self.lexer = PythonLexer()
        self.path_lexer = PathLexer()
        self.formatter = TerminalFormatter(colorscheme=self.colors)

        self.prompt = self._highlight("(Pdb) ", "purple")
        self.breakpoint_char = self._highlight("B", "purple")
        self.currentline_char = self._highlight("->", "purple")
        self.prompt_char = self._highlight(">>", "purple")
        self.line_prefix = f"\n{self._highlight('->', 'purple')} "
        self.prefix = self._highlight(">", "purple") + " "
        self.eof = self._highlight("[EOF]", "green")

    def _highlight(self, text: str, color: str) -> str:
        return f"\x1b[{self._colors[color]}m" + text + "\x1b[0m"

    def highlight_lines(self, lines: list[str]):
        whitespace = set(string.whitespace)

        for i in range(len(lines)):
            if not set(lines[i]).issubset(whitespace):
                first_non_whitespace_line = i
                break

        for i in range(len(lines) - 1, 0, -1):
            if not set(lines[i]).issubset(whitespace):
                last_non_whitespace_line = i
                break

        # Pygment's highlight function strips newlines at the start and end.
        # These lines are important so we add them back in later
        lines_highlighted = (
            highlight(
                "".join(lines[first_non_whitespace_line: last_non_whitespace_line + 1]),
                self.lexer,
                self.formatter
            )
            .strip("\n")
            .split("\n")
        )

        lines_highlighted = [line + "\n" for line in lines_highlighted]

        final = (
            lines[:first_non_whitespace_line]
            + lines_highlighted
            + lines[last_non_whitespace_line + 1:]
        )
        return final

    def _print_lines(self, lines, start, breaks=(), frame=None):
        filename = self.curframe.f_code.co_filename
        all_lines = linecache.getlines(filename, self.curframe.f_globals)
        lines_highlighted = self.highlight_lines(all_lines)

        if lines[0] == all_lines[start]:
            # The lines numbers start at 0, we add one to make the line numbers
            # start from 1
            super()._print_lines(
                lines_highlighted[start: start + len(lines)], start + 1, breaks, frame
            )
        else:
            # The lines numbers start at 1, we add one to make the line numbers
            # start from 0
            super()._print_lines(
                lines_highlighted[start - 1: start + len(lines)], start, breaks, frame
            )


    def print_stack_entry(self, frame_lineno, prompt_prefix=None):
        if prompt_prefix is None:
            prompt_prefix = self.line_prefix
        frame, lineno = frame_lineno
        if frame is self.curframe:
            prefix = self.prefix
        else:
            prefix = '  '
        self.message(prefix +
                     self.format_stack_entry(frame_lineno, prompt_prefix))

    def message(self, msg: str):
        if msg.startswith("\x1b"):
            # The message starts with a ANSI escape character so is probably
            # already highlight so needs no further text highlighting
            super().message(msg)
            return

        if msg == "[EOF]":
            super().message(self.eof)
            return

        msg = self.highlight_line_numbers_and_pdb_chars(msg)
        super().message(msg)

    def highlight_line_numbers_and_pdb_chars(self, msg):
        line_number_match = re.search(r"\d+", msg)

        if not line_number_match:
            return msg.rstrip()

        start, end = line_number_match.span()
        line_number = self._highlight(msg[start:end], "yellow")

        if msg[end + 2: end + 4] == "->":
            msg = msg[:start] + line_number + " " + self.currentline_char + " " + msg[end + 4:]
        elif msg[end + 2] == "B":
            msg = msg[:start] + line_number + " " + self.breakpoint_char + "  " + msg[end + 4:]
        else:
            msg = msg[:start] + line_number + msg[end:]

        return msg.rstrip()

    def format_stack_entry(self, frame_lineno, lprefix=': '):
        """Return a string with information about a stack entry.

        The stack entry frame_lineno is a (frame, lineno) tuple.  The
        return string contains the canonical filename, the function name
        or '<lambda>', the input arguments, the return value, and the
        line of code (if it exists).

        """
        frame, lineno = frame_lineno
        filename = self.canonic(frame.f_code.co_filename)
        s = '%s(%r)' % (filename, lineno)

        if frame.f_code.co_name:
            s += frame.f_code.co_name
        else:
            s += "<lambda>"
        s += '()'
        if '__return__' in frame.f_locals:
            rv = frame.f_locals['__return__']
            s += '->'
            s += reprlib.repr(rv)

        s = highlight(s, self.path_lexer, self.formatter).strip()
        line = linecache.getline(filename, lineno, frame.f_globals)
        if line:
            s += lprefix + line.strip()
        return s


class PathLexer(RegexLexer):
    name = "Path"
    alias = ["path"]
    filenames = ["*"]

    tokens = {
        "root": [
            (r'[^/()]+', Name.Attribute),  # Match everything but '/'
            (r'->', Generic.Subheading),  # Match '/'
            (r'[/()<>]', Generic.Subheading),  # Match '/'
        ]
    }


def set_trace():
    debugger = PdbColor()

    # The arguments here are copied from the PDB implementation of 'set_trace'
    debugger.set_trace(sys._getframe().f_back)
