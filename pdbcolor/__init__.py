from pdb import Pdb
import sys

from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import TerminalFormatter
from pygments.token import Operator, Literal, Text, Generic, Comment
from pygments.formatters.terminal import TERMINAL_COLORS
from pygments.filter import Filter


class PdbColor(Pdb):
    def __init__(self):
        super().__init__()
        self.colors = TERMINAL_COLORS.copy()
        self.colors[Comment] = ("green", "brightgreen")

        self.lexer = PythonLexer()
        self.lexer.add_filter(CurrentLineFilter())
        self.lexer.add_filter(LineNumberFilter())
        self.formatter = TerminalFormatter(colorscheme=self.colors)

    def highlight_lines(self, lines: list[str]):
        lines_highlighted = highlight("".join(lines), self.lexer, self.formatter)
        lines = lines_highlighted.split("\n")
        return lines

    def _print_lines(self, lines, start, breaks=(), frame=None):
        """Print a range of lines."""
        if frame:
            current_lineno = frame.f_lineno
            exc_lineno = self.tb_lineno.get(frame, -1)
        else:
            current_lineno = exc_lineno = -1
        formatted_lines = []
        for lineno, line in enumerate(lines, start):
            s = str(lineno).rjust(3)
            if len(s) < 4:
                s += " "
            if lineno in breaks:
                s += "B"
            else:
                s += " "
            if lineno == current_lineno:
                s += "->"
            elif lineno == exc_lineno:
                s += ">>"
            formatted_lines.append(s + "\t" + line.rstrip() + "\n")
            # self.message(s + '\t' + line.rstrip())
        highlighted_lines = self.highlight_lines(formatted_lines)
        for line in highlighted_lines:
            self.message(line)


class CurrentLineFilter(Filter):
    """Class for combining PDB's current line symbol ('->') into one token."""

    def __init__(self, **options):
        Filter.__init__(self, **options)

    def filter(self, lexer, stream):
        previous_token_was_subtract = False
        for ttype, value in stream:
            if previous_token_was_subtract:
                if ttype is Operator and value == ">":
                    # Combine '->' into one token
                    yield Generic.Subheading, "->"
                else:
                    # Yield previous subtract token and current token separately
                    yield Operator, "-"
                    yield ttype, value
                previous_token_was_subtract = False
            else:
                if ttype is Operator and value == "-":
                    previous_token_was_subtract = True
                else:
                    yield ttype, value


class LineNumberFilter(Filter):
    """Class for converting PDB's line numbers into tokens."""

    def __init__(self, **options):
        Filter.__init__(self, **options)

    def filter(self, lexer, stream):
        previous_token_was_newline = True

        for ttype, value in stream:
            if ttype is Text.Whitespace and value == "\n":
                previous_token_was_newline = True
                yield ttype, value
            elif previous_token_was_newline and ttype is Literal.Number.Integer:
                yield Literal.String, value
                previous_token_was_newline = False
            else:
                yield ttype, value


def set_trace():
    debugger = PdbColor()

    # The arguments here are copied from the PDB implementation of 'set_trace'
    debugger.set_trace(sys._getframe().f_back)
