
class CompilerError extends Error {
    constructor(message) {
        super(message);
        this.name = "CompilerError";
    }
}

class Diagnostics {
    constructor() {
        this.error_buffer = [];
        this.notes_buffer = [];
    }

    report_error(e, input_file = null, exec_info = null, fatal = true) {
        let info = exec_info || {};
        let line_num = info.num;
        let raw = info.raw;
        let ctx = info.ctx || "";
        let fname = input_file ? input_file.split('/').pop().split('\\').pop() : "SOURCE";

        let err_msg = "";

        if (raw == null) {
            err_msg = `error: ${e.message}\n`;
        } else {
            let leftPadLength = raw.length - raw.trimStart().length;
            let caret = " ".repeat(leftPadLength) + "^".repeat(Math.max(1, raw.trim().length));
            let pfx = " ".repeat(String(line_num).length + 1);
            let arw = " ".repeat(Math.max(1, String(line_num).length - 2));

            err_msg += `error: ${e.message}${ctx ? ` (inside ${ctx})` : ''}\n`;
            err_msg += `${arw}--> ${fname}:${line_num}\n${pfx}|\n`;
            err_msg += `${line_num} | ${raw.trimEnd()}\n${pfx}| ${caret}\n`;
        }

        if (fatal) {
            this.error_buffer.push(err_msg);
            throw new CompilerError(err_msg); // Throw to halt execution in JS
        } else {
            this.error_buffer.push(err_msg);
            if (this.error_buffer.length >= 50) {
                this.error_buffer.push(`error: Too many errors, aborting.\n`);
                throw new CompilerError("Too many errors");
            }
        }
    }

    check_errors() {
        if (this.error_buffer.length > 0) {
            throw new CompilerError(this.error_buffer.join('\n'));
        }
    }

    note(st) {
        this.notes_buffer.push(String(st));
    }

    get_notes() {
        let res = this.notes_buffer.join('');
        this.notes_buffer = [];
        return res;
    }

    reset() {
        this.error_buffer = [];
        this.notes_buffer = [];
    }
}

const _default_diagnostics = new Diagnostics();

function report_error(e, input_file = null, exec_info = null, fatal = true) {
    _default_diagnostics.report_error(e, input_file, exec_info, fatal);
}

function check_errors() {
    _default_diagnostics.check_errors();
}

function note(st) {
    _default_diagnostics.note(st);
}

function get_notes() {
    return _default_diagnostics.get_notes();
}

let _KEYWORDS = new Set();
let _SUGGESTION_KEYWORDS = [];

function setKeywords(keywordsList) {
    _SUGGESTION_KEYWORDS = keywordsList;
    _KEYWORDS.clear();
    for (let line_to_process of keywordsList) {
        if (!line_to_process.startsWith('"') && !line_to_process.startsWith("'")) {
            line_to_process = line_to_process.toLowerCase();
        }
        if (!line_to_process.endsWith('(') && !line_to_process.endsWith('.')) {
            _KEYWORDS.add(line_to_process);
        }
    }
}

function check_keyword(name) {
    if (_KEYWORDS.has(name)) {
        throw new CompilerError(`Name '${name}' is a reserved keyword`);
    }
}

function canonicalize(st) {
    let parts = st.trim().split(/(".*?")/);
    for (let i = 0; i < parts.length; i++) {
        if (i % 2 === 0) {
            parts[i] = parts[i].replace(/ *([^a-zA-Z0-9_]) */g, '$1');
        }
    }
    return parts.join('');
}

function del_inline_comment(line) {
    return line.split('#')[0].trimEnd();
}

// Tokenizer for safe_eval
function tokenize(expr) {
    let tokens = [];
    let i = 0;
    while (i < expr.length) {
        let char = expr[i];
        if (/\s/.test(char)) {
            i++;
            continue;
        }
        if (/[a-zA-Z_]/.test(char)) {
            let id = "";
            while (i < expr.length && /[a-zA-Z0-9_]/.test(expr[i])) {
                id += expr[i];
                i++;
            }
            tokens.push({ type: 'ID', value: id });
            continue;
        }
        if (/[0-9]/.test(char) || (char === '.' && i + 1 < expr.length && /[0-9]/.test(expr[i+1]))) {
            let num = "";
            let isHex = false;
            if (char === '0' && (expr[i+1] === 'x' || expr[i+1] === 'X')) {
                isHex = true;
                num = "0x";
                i += 2;
                while (i < expr.length && /[0-9a-fA-F]/.test(expr[i])) {
                    num += expr[i];
                    i++;
                }
            } else {
                while (i < expr.length && /[0-9.]/.test(expr[i])) {
                    num += expr[i];
                    i++;
                }
            }
            tokens.push({ type: 'NUM', value: isHex ? parseInt(num, 16) : parseFloat(num) });
            continue;
        }
        if (char === '"' || char === "'") {
            let quote = char;
            let str = "";
            i++;
            while (i < expr.length && expr[i] !== quote) {
                str += expr[i];
                i++;
            }
            i++; // skip closing quote
            tokens.push({ type: 'STR', value: str });
            continue;
        }
        // Multi-char operators
        let op2 = expr.substring(i, i + 2);
        if (op2 === '//' || op2 === '**' || op2 === '<<' || op2 === '>>' || op2 === '==') {
            tokens.push({ type: 'OP', value: op2 });
            i += 2;
            continue;
        }
        if (/[+\-*/%^&|~()<>[\],]/.test(char)) {
            tokens.push({ type: 'OP', value: char });
            i++;
            continue;
        }
        throw new CompilerError(`Unknown token: ${char}`);
    }
    return tokens;
}

// Pratt Parser for safe_eval
function parseAndEval(tokens, scope) {
    let pos = 0;

    function peek() {
        return pos < tokens.length ? tokens[pos] : null;
    }

    function consume(type, value = null) {
        let t = peek();
        if (t && t.type === type && (value === null || t.value === value)) {
            pos++;
            return t;
        }
        return null;
    }

    function expect(type, value = null) {
        let t = consume(type, value);
        if (!t) {
            throw new CompilerError(`Expected ${value || type}`);
        }
        return t;
    }

    function parsePrimary() {
        let t = peek();
        if (!t) throw new CompilerError("Unexpected end of expression");

        if (t.type === 'NUM' || t.type === 'STR') {
            consume(t.type);
            return t.value;
        }
        if (t.type === 'ID') {
            consume('ID');
            // Function call
            if (consume('OP', '(')) {
                let args = [];
                if (!consume('OP', ')')) {
                    while (true) {
                        args.push(parseExpression(0));
                        if (consume('OP', ',')) continue;
                        if (consume('OP', ')')) break;
                        throw new CompilerError("Expected ',' or ')' in function call");
                    }
                }
                let func = scope[t.value];
                if (typeof func !== 'function') {
                    throw new CompilerError(`Not callable: ${t.value}`);
                }
                return func(...args);
            }
            // Variable access
            return scope[t.value] !== undefined ? scope[t.value] : 0;
        }
        if (consume('OP', '(')) {
            let expr = parseExpression(0);
            expect('OP', ')');
            return expr;
        }
        if (consume('OP', '[')) {
            let elements = [];
            if (!consume('OP', ']')) {
                while (true) {
                    elements.push(parseExpression(0));
                    if (consume('OP', ',')) continue;
                    if (consume('OP', ']')) break;
                    throw new CompilerError("Expected ',' or ']' in array literal");
                }
            }
            return elements;
        }
        if (consume('OP', '-')) return -parsePrimary();
        if (consume('OP', '+')) return parsePrimary();
        if (consume('OP', '~')) return ~parsePrimary();

        throw new CompilerError(`Unexpected token: ${t.value}`);
    }

    const precedence = {
        '|': 1,
        '^': 2,
        '&': 3,
        '<<': 4, '>>': 4,
        '+': 5, '-': 5,
        '*': 6, '/': 6, '//': 6, '%': 6,
        '**': 7
    };

    function parseExpression(minPrec) {
        let left = parsePrimary();

        while (true) {
            let t = peek();
            if (!t || t.type !== 'OP' || !(t.value in precedence) || precedence[t.value] < minPrec) {
                break;
            }
            let op = consume('OP').value;
            let prec = precedence[op];
            let right = parseExpression(op === '**' ? prec : prec + 1); // Right-associative for **

            if (op === '+') left = left + right;
            else if (op === '-') left = left - right;
            else if (op === '*') left = left * right;
            else if (op === '/') left = left / right;
            else if (op === '//') left = Math.floor(left / right);
            else if (op === '%') left = left % right;
            else if (op === '**') left = Math.pow(left, right);
            else if (op === '<<') left = left << right;
            else if (op === '>>') left = left >> right;
            else if (op === '|') left = left | right;
            else if (op === '^') left = left ^ right;
            else if (op === '&') left = left & right;
        }
        return left;
    }

    let result = parseExpression(0);
    if (pos < tokens.length) {
        throw new CompilerError(`Unexpected token after expression: ${tokens[pos].value}`);
    }
    return result;
}

function safe_eval(expr_str, scope = {}) {
    try {
        let tokens = tokenize(expr_str);
        return parseAndEval(tokens, scope);
    } catch (e) {
        throw new CompilerError(`Eval error: ${expr_str} - ${e.message}`);
    }
}

export {
    CompilerError,
    report_error,
    check_errors,
    note,
    get_notes,
    setKeywords,
    check_keyword,
    canonicalize,
    del_inline_comment,
    safe_eval,
    _default_diagnostics
};
