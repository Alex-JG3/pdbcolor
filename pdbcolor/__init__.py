from pdb import Pdb
import sys
import re
import linecache
import string
import rlcompleter

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
        self.line_prefix = self._highlight('->', 'purple')
        self._return = self._highlight("--Return--", "green")
        self.prefix = self._highlight(">", "purple") + " "
        self.eof = self._highlight("[EOF]", "green")
        self.tag = ":TAG:"

    def _highlight(self, text: str, color: str) -> str:
        return f"\x1b[{self._colors[color]}m" + text + "\x1b[0m"

    # Autocomplete
    complete = rlcompleter.Completer(locals()).complete

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

        # Add tag to the end of each line to allow code lines to be more easily
        # identified
        lines_highlighted = [
            line + "\n" + self.tag for line in lines_highlighted
        ]

        final = (
            lines[:first_non_whitespace_line]
            + lines_highlighted
            + lines[last_non_whitespace_line + 1:]
        )
        return final

    def _print_lines(self, lines, start, breaks=(), frame=None):
        if len(lines) == 0:
            super()._print_lines(lines, start, breaks, frame)
            return

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


    def message(self, msg: str):
        if msg.endswith(self.tag):
            msg = self.highlight_line_numbers_and_pdb_chars(self.remove_tag(msg))
            super().message(msg)
        elif msg[0] == ">":
            path, current_line = msg.split("\n")
            path = self.prefix + highlight(path[2:], self.path_lexer, self.formatter)
            current_line = self.line_prefix + " " + current_line[3:]
            super().message(path + current_line)
        elif msg == "--Return--":
            super().message(self._return)
        elif msg == "[EOF]":
            super().message(self.eof)
        else:
            super().message(msg)

    def remove_tag(self, text):
        return text[:-5]

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
