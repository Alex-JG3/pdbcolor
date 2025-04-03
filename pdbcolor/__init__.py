from pdb import Pdb
import sys
import linecache
import reprlib

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
        self.breakpoint_char = self._highlight("B", "red")
        self.currentline_char = self._highlight("->", "red")
        self.prompt_char = self._highlight(">>", "purple")
        self.line_prefix = f"\n{self._highlight('->', 'purple')} "
        self.prefix = self._highlight(">", "purple") + " "
        self.eof = self._highlight("[EOF]", "green")

    def _highlight(self, text: str, color: str) -> str:
        return f"\x1b[{self._colors[color]}m" + text + "\x1b[0m"

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
            s = self._highlight(str(lineno), "yellow").rjust(3)
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
                self.message(self.eof)
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
