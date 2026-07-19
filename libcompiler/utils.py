import sys
import os
import re
import ast
import operator
from typing import Any, Dict, List, Optional, Union, Callable
from libcompiler.i18n import t

def get_os_info() -> str:
    """Returns a string identifying the current operating system."""
    if hasattr(sys, 'getandroidapilevel') or os.environ.get('PREFIX') == '/data/data/com.termux/files/usr':
        return "Android (Termux)"
    elif sys.platform.startswith('win'):
        return "Windows"
    elif sys.platform.startswith('darwin'):
        return "MacOS"
    elif sys.platform.startswith('linux'):
        return "Linux"
    else:
        return "Unknown OS"

class CompilerError(Exception):
    """Exception raised for errors during compilation."""
    pass

class TerminalColors:
    """Helper class for terminal ANSI escape codes."""
    def __init__(self, use_colors: bool):
        self.RED = '\033[1;31m' if use_colors else ''
        self.BLUE = '\033[1;34m' if use_colors else ''
        self.BOLD = '\033[1m' if use_colors else ''
        self.RESET = '\033[0m' if use_colors else ''

class Diagnostics:
    """Manages compiler errors, warnings, and notes."""
    def __init__(self):
        self.error_buffer: List[str] = []
        self.notes_buffer: List[str] = []
        self.use_colors: bool = self._check_tty()
        self.colors = TerminalColors(self.use_colors)

    def _check_tty(self) -> bool:
        """Determines if stderr supports colors."""
        is_tty = sys.stderr.isatty()
        if is_tty and get_os_info() == 'Windows':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                h_err = kernel32.GetStdHandle(-12)
                mode = ctypes.c_ulong()
                if kernel32.GetConsoleMode(h_err, ctypes.byref(mode)):
                    kernel32.SetConsoleMode(h_err, mode.value | 0x0004)
            except Exception:
                is_tty = False
        return is_tty

    def report_error(self, e: Exception, input_file: Optional[str] = None, exec_info: Optional[Dict[str, Any]] = None, fatal: bool = True) -> None:
        """Reports a compilation error, optionally halting execution."""
        info = exec_info or {}
        line_num = info.get("num")
        raw = info.get("raw")
        ctx = info.get("ctx", "")
        fname = os.path.basename(input_file) if input_file else "source".upper()
        
        c = self.colors
        err_msg = ""
        
        if raw is None:
            err_msg = f"\n{c.RED}{c.BOLD}error:{c.RESET} {c.BOLD}{str(e)}{c.RESET}\n\n"
        else:
            caret = " " * (len(raw) - len(raw.lstrip())) + "^" * max(1, len(raw.strip()))
            pfx = " " * (len(str(line_num)) + 1)
            arw = " " * max(1, len(str(line_num)) - 2)

            err_msg += f"\n{c.RED}{c.BOLD}error:{c.RESET} {c.BOLD}{str(e)}{f' (inside {ctx})' if ctx else ''}{c.RESET}\n"
            err_msg += f"{arw}{c.BLUE}-->{c.RESET} {fname}:{line_num}\n{pfx}{c.BLUE}|{c.RESET}\n"
            err_msg += f"{c.BLUE}{line_num} |{c.RESET} {raw.rstrip()}\n{pfx}{c.BLUE}|{c.RESET} {c.RED}{caret}{c.RESET}\n\n"

        if fatal:
            self._flush_errors()
            sys.stderr.write(err_msg)
            sys.exit(1)
        else:
            self.error_buffer.append(err_msg)
            if len(self.error_buffer) >= 50:
                self.error_buffer.append(f"\n{c.RED}{c.BOLD}error:{c.RESET} {c.BOLD}Too many errors, aborting.{c.RESET}\n\n")
                self.check_errors()

    def _flush_errors(self) -> None:
        """Writes buffered errors to stderr and clears the buffer."""
        for err in self.error_buffer:
            sys.stderr.write(err)
        self.error_buffer.clear()

    def check_errors(self) -> None:
        """Exits the program if there are buffered errors."""
        if self.error_buffer:
            self._flush_errors()
            sys.exit(1)

    def note(self, st: Any) -> None:
        """Adds a note to the current buffer."""
        self.notes_buffer.append(str(st))

    def get_notes(self) -> str:
        """Returns buffered notes and clears the buffer."""
        res = ''.join(self.notes_buffer)
        self.notes_buffer.clear()
        return res

    def reset(self) -> None:
        """Clears all internal buffers."""
        self.error_buffer.clear()
        self.notes_buffer.clear()


# Default diagnostics instance for backward compatibility
_default_diagnostics = Diagnostics()
error_buffer = _default_diagnostics.error_buffer # Kept for backward compatibility if directly mutated
notes_buffer = _default_diagnostics.notes_buffer

def report_error(e: Exception, input_file: Optional[str] = None, exec_info: Optional[Dict[str, Any]] = None, fatal: bool = True) -> None:
    _default_diagnostics.report_error(e, input_file, exec_info, fatal)

def check_errors() -> None:
    _default_diagnostics.check_errors()

def note(st: Any) -> None:
    _default_diagnostics.note(st)

def get_notes() -> str:
    return _default_diagnostics.get_notes()

_KEYWORDS = set()
_SUGGESTION_KEYWORDS = []
try:
    _keyword_path = os.path.join(os.path.dirname(__file__), "keyword.txt")
    with open(_keyword_path, "r", encoding="utf-8") as _f:
        lines = [line.strip() for line in _f if line.strip()]
        _SUGGESTION_KEYWORDS = lines
        _KEYWORDS = set()
        for line_to_process in lines:
            if not line_to_process.startswith('"') and not line_to_process.startswith("'"):
                line_to_process = line_to_process.lower()
            if not line_to_process.endswith('(') and not line_to_process.endswith('.'):
                _KEYWORDS.add(line_to_process)
except Exception:
    pass

def check_keyword(name: str) -> None:
    """Checks if the given name is a reserved keyword and raises a CompilerError if it is."""
    if name in _KEYWORDS:
        raise CompilerError(t("err_reserved_keyword", name=name))


# Utility Functions
def canonicalize(st: str) -> str:
    """Removes spaces around non-alphanumeric characters, except within string literals."""
    return ''.join(re.sub(r' *([^a-zA-Z0-9_]) *', r'\1', p) if i % 2 == 0 else p 
                   for i, p in enumerate(re.split(r'(".*?")', st.strip())))

def del_inline_comment(line: str) -> str:
    """Strips inline comments starting with '#' from a line."""
    return line.split('#')[0].rstrip()

_OPS: Dict[type, Callable] = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
    ast.Pow: operator.pow, ast.LShift: operator.lshift, ast.RShift: operator.rshift,
    ast.BitOr: operator.or_, ast.BitXor: operator.xor, ast.BitAnd: operator.and_,
    ast.UAdd: operator.pos, ast.USub: operator.neg, ast.Invert: operator.invert
}

def safe_eval(expr_str: str, scope: Optional[Dict[str, Any]] = None) -> Any:
    """Safely evaluates a Python expression using AST parsing."""
    scope_dict = scope or {}
    
    def _eval(node: ast.AST) -> Any:
        if isinstance(node, ast.Expression): 
            return _eval(node.body)
        elif isinstance(node, ast.Constant): 
            return node.value
        elif isinstance(node, ast.Name): 
            return scope_dict.get(node.id, 0)
        elif isinstance(node, ast.BinOp):
            if isinstance(node.op, ast.Pow) and (right := _eval(node.right)) > 1000:
                raise CompilerError(t("err_exponent_too_large_memory_9c48"))
            return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp): 
            return _OPS[type(node.op)](_eval(node.operand))
        elif isinstance(node, (ast.List, ast.Tuple)): 
            return [_eval(x) for x in node.elts]
        elif isinstance(node, ast.Call):
            func = _eval(node.func)
            if not callable(func): 
                raise CompilerError(t("err_not_callable_var0_9525", var0=func))
            args = [_eval(a) for a in node.args]
            kwargs = {k.arg: _eval(k.value) for k in node.keywords if k.arg is not None}
            return func(*args, **kwargs)
        elif isinstance(node, ast.Attribute):
            obj = _eval(node.value)
            if callable(obj): 
                return obj(node.attr)
            raise CompilerError(t("err_unsupported_attribute_access_var0_c87f", var0=node.attr))
        
        raise CompilerError(t("err_unsupported_syntax_var0_ce11", var0=type(node).__name__))
    
    try: 
        return _eval(ast.parse(expr_str.strip(), mode='eval'))
    except Exception as e: 
        raise CompilerError(t("err_eval_error_var0_var1_d3b7", var0=expr_str, var1=e))
