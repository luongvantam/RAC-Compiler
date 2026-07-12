import sys
import os
import re
import ast
import operator

def get_os_info():
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
    pass

error_buffer = []

def report_error(e, input_file=None, exec_info=None, fatal=True):
    info = exec_info or {}
    line_num = info.get("num")
    raw = info.get("raw")
    ctx = info.get("ctx", "")
    fname = os.path.basename(input_file) if input_file else "source".upper()
    
    is_tty = sys.stderr.isatty()
    if is_tty and get_os_info() == 'Windows':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            h_err, mode = kernel32.GetStdHandle(-12), ctypes.c_ulong()
            if kernel32.GetConsoleMode(h_err, ctypes.byref(mode)): kernel32.SetConsoleMode(h_err, mode.value | 0x0004)
        except Exception: is_tty = False

    c_red, c_blu, c_bld, c_rst = ('\033[1;31m', '\033[1;34m', '\033[1m', '\033[0m') if is_tty else ('', '', '', '')

    err_msg = ""
    if raw is None:
        err_msg = f"\n{c_red}{c_bld}error:{c_rst} {c_bld}{str(e)}{c_rst}\n\n"
    else:
        caret = " " * (len(raw) - len(raw.lstrip())) + "^" * max(1, len(raw.strip()))
        pfx, arw = " " * (len(str(line_num)) + 1), " " * max(1, len(str(line_num)) - 2)

        err_msg += f"\n{c_red}{c_bld}error:{c_rst} {c_bld}{str(e)}{f' (inside {ctx})' if ctx else ''}{c_rst}\n"
        err_msg += f"{arw}{c_blu}-->{c_rst} {fname}:{line_num}\n{pfx}{c_blu}|{c_rst}\n"
        err_msg += f"{c_blu}{line_num} |{c_rst} {raw.rstrip()}\n{pfx}{c_blu}|{c_rst} {c_red}{caret}{c_rst}\n\n"

    if fatal:
        for err in error_buffer:
            sys.stderr.write(err)
        error_buffer.clear()
        sys.stderr.write(err_msg)
        sys.exit(1)
    else:
        error_buffer.append(err_msg)
        if len(error_buffer) >= 50:
            error_buffer.append(f"\n{c_red}{c_bld}error:{c_rst} {c_bld}Too many errors, aborting.{c_rst}\n\n")
            check_errors()

def check_errors():
    if error_buffer:
        for err in error_buffer:
            sys.stderr.write(err)
        error_buffer.clear()
        sys.exit(1)

notes_buffer = []
def note(st): notes_buffer.append(str(st))
def get_notes():
    res = ''.join(notes_buffer)
    notes_buffer.clear()
    return res

def canonicalize(st):
    return ''.join(re.sub(r' *([^a-z0-9]) *', r'\1', p) if i % 2 == 0 else p for i, p in enumerate(re.split(r'(".*?")', st.strip())))

def del_inline_comment(line):
    return line.split('#')[0].rstrip()


_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
    ast.Pow: operator.pow, ast.LShift: operator.lshift, ast.RShift: operator.rshift,
    ast.BitOr: operator.or_, ast.BitXor: operator.xor, ast.BitAnd: operator.and_,
    ast.UAdd: operator.pos, ast.USub: operator.neg, ast.Invert: operator.invert
}

def safe_eval(expr_str, scope=None):
    scope = scope or {}
    def _eval(node):
        if isinstance(node, ast.Expression): return _eval(node.body)
        elif isinstance(node, ast.Constant): return node.value
        elif isinstance(node, ast.Name): return scope.get(node.id, 0)
        elif isinstance(node, ast.BinOp):
            if isinstance(node.op, ast.Pow) and (right := _eval(node.right)) > 1000:
                raise CompilerError("Exponent too large (Memory Protection)")
            return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp): return _OPS[type(node.op)](_eval(node.operand))
        elif isinstance(node, (ast.List, ast.Tuple)): return [_eval(x) for x in node.elts]
        elif isinstance(node, ast.Call):
            func = _eval(node.func)
            if not callable(func): raise CompilerError(f"Not callable: {func}")
            return func(*[_eval(a) for a in node.args], **{k.arg: _eval(k.value) for k in node.keywords})
        elif isinstance(node, ast.Attribute):
            obj = _eval(node.value)
            if callable(obj): return obj(node.attr)
            raise CompilerError(f"Unsupported attribute access: {node.attr}")
        raise CompilerError(f"Unsupported syntax: {type(node).__name__}")
    
    try: return _eval(ast.parse(expr_str.strip(), mode='eval'))
    except Exception as e: raise CompilerError(f"Eval error: {expr_str} - {e}")
