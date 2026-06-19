import sys
import re
import ast
import operator

def default_note(st):
    ''' Print st to stderr. Used for additional information (note, warning) '''
    sys.stderr.write(st)

note = default_note

def to_lowercase(s):
    return s.lower()

def canonicalize(st):
    st = st.strip()
    parts = re.split(r'(".*?")', st)  
    for i in range(len(parts)):
        if i % 2 == 0:
            parts[i] = re.sub(r' *([^a-z0-9]) *', r'\1', parts[i])
    return ''.join(parts)

def del_inline_comment(line):
    return (line + '#')[:line.find('#')].rstrip()

# Define safe operators for AST evaluation
SAFE_OPERATORS = {
    # Binary operators
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.LShift: operator.lshift,
    ast.RShift: operator.rshift,
    ast.BitOr: operator.or_,
    ast.BitXor: operator.xor,
    ast.BitAnd: operator.and_,
    # Unary operators
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
    ast.Invert: operator.inv,
    ast.Not: operator.not_,
    # Comparison operators
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}

def safe_eval(expr_str, scope=None):
    if scope is None:
        scope = {}
    
    try:
        node = ast.parse(expr_str.strip(), mode='eval')
    except SyntaxError as e:
        raise ValueError(f"Syntax error in expression: {e}")

    def eval_node(node):
        if isinstance(node, ast.Expression):
            return eval_node(node.body)
        elif hasattr(ast, 'Constant') and isinstance(node, ast.Constant): # Python 3.8+
            return node.value
        elif hasattr(ast, 'Num') and isinstance(node, ast.Num): # Python < 3.8
            return node.n
        elif hasattr(ast, 'Str') and isinstance(node, ast.Str): # Python < 3.8
            return node.s
        elif hasattr(ast, 'NameConstant') and isinstance(node, ast.NameConstant): # Python < 3.8
            return node.value
        elif isinstance(node, ast.Name):
            if node.id in scope:
                return scope[node.id]
            raise NameError(f"Name {node.id!r} is not defined")
        elif isinstance(node, ast.BinOp):
            left = eval_node(node.left)
            right = eval_node(node.right)
            op_type = type(node.op)
            if op_type in SAFE_OPERATORS:
                return SAFE_OPERATORS[op_type](left, right)
            raise TypeError(f"Unsupported binary operator: {op_type.__name__}")
        elif isinstance(node, ast.UnaryOp):
            operand = eval_node(node.operand)
            op_type = type(node.op)
            if op_type in SAFE_OPERATORS:
                return SAFE_OPERATORS[op_type](operand)
            raise TypeError(f"Unsupported unary operator: {op_type.__name__}")
        elif isinstance(node, ast.BoolOp):
            values = [eval_node(val) for val in node.values]
            if isinstance(node.op, ast.And):
                res = True
                for val in values:
                    res = res and val
                    if not res:
                        break
                return res
            elif isinstance(node.op, ast.Or):
                res = False
                for val in values:
                    res = res or val
                    if res:
                        break
                return res
            raise TypeError(f"Unsupported logical operator: {type(node.op).__name__}")
        elif isinstance(node, ast.Compare):
            left = eval_node(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                right = eval_node(comparator)
                op_type = type(op)
                if op_type in SAFE_OPERATORS:
                    if not SAFE_OPERATORS[op_type](left, right):
                        return False
                    left = right
                else:
                    raise TypeError(f"Unsupported comparison operator: {op_type.__name__}")
            return True
        elif isinstance(node, ast.Call):
            func = eval_node(node.func)
            if not callable(func):
                raise TypeError(f"Function {node.func!r} is not callable")
            args = [eval_node(arg) for arg in node.args]
            keywords = {kw.arg: eval_node(kw.value) for kw in node.keywords}
            return func(*args, **keywords)
        elif isinstance(node, ast.Subscript):
            value = eval_node(node.value)
            if hasattr(ast, 'Index') and isinstance(node.slice, ast.Index):
                index = eval_node(node.slice.value)
            else:
                index = eval_node(node.slice)
            return value[index]
        elif isinstance(node, ast.Slice):
            lower = eval_node(node.lower) if node.lower is not None else None
            upper = eval_node(node.upper) if node.upper is not None else None
            step = eval_node(node.step) if node.step is not None else None
            return slice(lower, upper, step)
        elif isinstance(node, ast.Tuple):
            return tuple(eval_node(el) for el in node.elts)
        elif isinstance(node, ast.List):
            return list(eval_node(el) for el in node.elts)
        elif isinstance(node, ast.Dict):
            keys = [eval_node(k) for k in node.keys]
            values = [eval_node(v) for v in node.values]
            return dict(zip(keys, values))
        elif isinstance(node, ast.FormattedValue):
            value = eval_node(node.value)
            if node.conversion == 115: # !s
                value = str(value)
            elif node.conversion == 114: # !r
                value = repr(value)
            elif node.conversion == 97: # !a
                value = ascii(value)
            if node.format_spec:
                fmt = eval_node(node.format_spec)
                return format(value, fmt)
            return value
        elif isinstance(node, ast.JoinedStr):
            return "".join(str(eval_node(value)) for value in node.values)
        else:
            raise TypeError(f"Unsupported syntax tree node: {type(node).__name__}")

    return eval_node(node)
