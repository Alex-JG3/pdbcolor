from pdb import Pdb
import sys
import linecache

from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.lexer import RegexLexer
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
        self.formatter = TerminalFormatter(colorscheme=self.colors)

        self.pdb_lexer = PdbLexer()
        self.prompt = highlight("(Pdb)", self.pdb_lexer, self.formatter).rstrip() + " "
        self.breakpoint_char = highlight("B", self.pdb_lexer, self.formatter).rstrip()
        self.currentline_char = highlight("->", self.pdb_lexer, self.formatter).rstrip()
        self.prompt_char = highlight(">>", self.pdb_lexer, self.formatter).rstrip()
        self.line_prefix = f"\n{self.currentline_char} "
        self.prefix = highlight(">", self.pdb_lexer, self.formatter).rstrip() + " "

    def highlight_lines(self, lines: list[str]):
        lines_highlighted = highlight("".join(lines), self.lexer, self.formatter)
        lines = lines_highlighted.split("\n")
        return lines

    def _print_lines(self, lines, start, breaks=(), frame=None, highlight=True):
        """Print a range of lines."""
        if highlight:
            lines = self.highlight_lines(lines)
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
                s += self.breakpoint_char
            else:
                s += " "
            if lineno == current_lineno:
                s += self.currentline_char
            elif lineno == exc_lineno:
                s += self.prompt_char
            formatted_lines.append(s + "\t" + line.rstrip())
        for line in formatted_lines:
            self.message(line)

    def do_list(self, arg):
        """l(ist) [first [,last] | .]

        List source code for the current file.  Without arguments,
        list 11 lines around the current line or continue the previous
        listing.  With . as argument, list 11 lines around the current
        line.  With one argument, list 11 lines starting at that line.
        With two arguments, list the given range; if the second
        argument is less than the first, it is a count.

        The current line in the current frame is indicated by "->".
        If an exception is being debugged, the line where the
        exception was originally raised or propagated is indicated by
        ">>", if it differs from the current line.
        """
        self.lastcmd = "list"
        last = None
        if arg and arg != ".":
            try:
                if "," in arg:
                    first, last = arg.split(",")
                    first = int(first.strip())
                    last = int(last.strip())
                    if last < first:
                        # assume it's a count
                        last = first + last
                else:
                    first = int(arg.strip())
                    first = max(1, first - 5)
            except ValueError:
                self.error("Error in argument: %r" % arg)
                return
        elif self.lineno is None or arg == ".":
            first = max(1, self.curframe.f_lineno - 5)
        else:
            first = self.lineno + 1
        if last is None:
            last = first + 10
        filename = self.curframe.f_code.co_filename
        breaklist = self.get_file_breaks(filename)
        try:
            lines = linecache.getlines(filename, self.curframe.f_globals)

            # Highlight lines before '_print_lines' to ensure they are
            # highlighted correctly
            lines = self.highlight_lines(lines)

            self._print_lines(
                lines[first - 1 : last],
                first,
                breaklist,
                self.curframe,
                highlight=False,
            )
            self.lineno = min(last, len(lines))
            if len(lines) < last:
                self.message("[EOF]")
        except KeyboardInterrupt:
            pass

    do_l = do_list

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


class PdbLexer(RegexLexer):
    name = "Pdb"
    alias = ["pdb"]
    filenames = ["*"]

    tokens = {
        "root": [
            (r"\(Pdb\)", Generic.Subheading),
            (r"->", Generic.Subheading),
            (r">>", Generic.Subheading),
            (r">", Generic.Subheading),
            (r"B", Generic.Subheading),
        ]
    }


def set_trace():
    debugger = PdbColor()

    # The arguments here are copied from the PDB implementation of 'set_trace'
    debugger.set_trace(sys._getframe().f_back)
