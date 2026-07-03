import re
import ast
import operator

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
                raise ValueError("Exponent too large (Memory Protection)")
            return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp): return _OPS[type(node.op)](_eval(node.operand))
        elif isinstance(node, (ast.List, ast.Tuple)): return [_eval(x) for x in node.elts]
        raise ValueError(f"Unsupported syntax: {type(node).__name__}")
    
    try: return _eval(ast.parse(expr_str.strip(), mode='eval'))
    except Exception as e: raise ValueError(f"Eval error: {expr_str} - {e}")
