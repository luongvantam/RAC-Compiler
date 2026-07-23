import * as utils from './utils.js';
import * as loader from './loader.js';

let sorted_tokens = [];

function init_handlers() {
    sorted_tokens = Object.keys(loader.token_to_hex).sort((a, b) => b.length - a.length);
}

function register_alias(name, target) {
    loader.aliases[name] = target;
    loader.set_state('aliases_pattern', null); // Invalidate cache
}

function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); // $& means the whole matched string
}

function run_alias(line) {
    if (Object.keys(loader.aliases).length === 0) return line;
    if (!loader.aliases_pattern) {
        let pattern_str = '\\b(' + Object.keys(loader.aliases).map(escapeRegExp).join('|') + ')\\b';
        loader.set_state('aliases_pattern', new RegExp(pattern_str, 'g'));
    }

    let parts = line.split(/("[^"\\]*(?:\\.[^"\\]*)*"|'[^'\\]*(?:\\.[^'\\]*)*')/);
    for (let i = 0; i < parts.length; i += 2) {
        parts[i] = parts[i].replace(loader.aliases_pattern, (match, p1) => loader.aliases[p1]);
    }
    return parts.join('');
}

function add_macro(pattern, rest, program_iter) {
    let body_items;
    if (rest.startsWith('{')) {
        let res = collect_block_body(rest.substring(1), program_iter);
        body_items = res[0];
    } else {
        body_items = rest ? [rest] : [];
    }

    let body_lines = body_items.map(item => {
        if (Array.isArray(item) && item.length === 2) return item[1];
        if (typeof item === 'object' && item !== null && item.exec) return item.exec;
        return String(item);
    });

    let canonical_pat = utils.canonicalize(pattern);
    let converted_pat = escapeRegExp(canonical_pat).replace(/\\\</g, "(?<").replace(/</g, "(?<").replace(/\\\>/g, ">.+?)").replace(/>/g, ">.+?)");

    let keyword = pattern.split('<')[0].trim();
    let m_kw = keyword.match(/^([a-zA-Z_]\w*)/);
    let macro_keyword = utils.canonicalize(m_kw ? m_kw[1] : keyword.replace(/\(/g, '').trim());

    loader.dynamic_macros.push({
        pattern: pattern,
        keyword: macro_keyword,
        compiled_pattern: new RegExp(converted_pat),
        output: body_lines
    });
    loader.dynamic_macros.sort((a, b) => b.pattern.length - a.pattern.length);
}

function run_macro(line_strip, line_num, remaining_lines) {
    if (loader.dynamic_macros.length === 0) return false;

    for (let macro of loader.dynamic_macros) {
        if (!line_strip.includes(macro.keyword)) continue;
        let match = macro.compiled_pattern.exec(line_strip);
        if (match) {
            let local_env = match.groups || {};
            let output_lines = [];
            for (let out of macro.output) {
                let temp = out;
                for (let [k, v] of Object.entries(local_env)) {
                    temp = temp.replace(new RegExp(`<${k}>`, 'g'), String(v));
                }
                output_lines.push(temp);
            }

            if (output_lines.length === 1) {
                let replaced_line = line_strip.substring(0, match.index) + output_lines[0] + line_strip.substring(match.index + match[0].length);
                remaining_lines.unshift([line_num, replaced_line]);
            } else {
                for (let i = output_lines.length - 1; i >= 0; i--) {
                    remaining_lines.unshift([line_num, output_lines[i]]);
                }
            }
            return true;
        }
    }
    return false;
}

function run_func(line_strip, raw_line, line_num, final_lines_to_process) {
    let m = line_strip.match(/^(\w+)\s*\(((?:[^()]+|\([^()]*\))*)\)/);
    if (!m || !(m[1] in loader.defined_functions)) return false;

    let called_func_name = m[1];
    let call_args_str = m[2];
    let func = loader.defined_functions[called_func_name];

    let call_args = [];
    let regex = /("(?:[^"\\]|\\.)*"|[^,]+)/g;
    let match;
    while ((match = regex.exec(call_args_str)) !== null) {
        call_args.push(match[1].trim());
    }
    if (call_args.length === 1 && call_args[0] === '' && !call_args_str) call_args = [];

    let params = func.params;
    let required = params.filter(p => p[1] === null).length;
    if (call_args.length > params.length || call_args.length < required) {
        throw new utils.CompilerError(`Args mismatch: ${line_strip}`);
    }

    let bound = [...call_args];
    for (let i = bound.length; i < params.length; i++) {
        bound.push(params[i][1]);
    }

    if ("return_expr" in func) {
        let ret_expr = func.return_expr;
        for (let i = 0; i < params.length; i++) {
            let param = params[i][0];
            let arg = bound[i];
            let parts = ret_expr.split(/("[^"\\]*(?:\\.[^"\\]*)*"|'[^'\\]*(?:\\.[^'\\]*)*')/);
            for (let j = 0; j < parts.length; j += 2) {
                parts[j] = parts[j].replace(new RegExp(`\\b${escapeRegExp(param)}\\b`, 'g'), arg);
            }
            ret_expr = parts.join('');
        }
        final_lines_to_process.push({ exec: ret_expr, raw: raw_line, num: line_num, ctx: `inside '${called_func_name}'` });
        return true;
    }

    for (let i = 0; i < params.length; i++) {
        let param = params[i][0].trim();
        let arg_val = bound[i];
        if (param) {
            final_lines_to_process.push({ exec: `var ${param} = ${arg_val}`, raw: raw_line, num: line_num, ctx: `passing args to '${called_func_name}'` });
        }
    }

    for (let item of func.body) {
        let f_line_num = Array.isArray(item) ? item[0] : line_num;
        let line_in_func = Array.isArray(item) ? item[1] : item;
        final_lines_to_process.push({ exec: line_in_func, raw: line_in_func, num: f_line_num, ctx: `inside '${called_func_name}'` });
    }
    return true;
}

function split_lines(line) {
    let parts = [];
    let current = [];
    let in_double = false;
    let in_single = false;
    for (let i = 0; i < line.length; i++) {
        let char = line[i];
        if (char === '"' && !in_single && (i === 0 || line[i - 1] !== '\\')) in_double = !in_double;
        else if (char === "'" && !in_double && (i === 0 || line[i - 1] !== '\\')) in_single = !in_single;
        else if (char === ';' && !in_double && !in_single) {
            parts.push(current.join('').trim());
            current = [];
            continue;
        }
        current.push(char);
    }
    parts.push(current.join('').trim());
    return parts.filter(p => p);
}

function merge_lines(program_lines) {
    let final_merged = [];
    let current_line = "";
    let current_num = null;
    let paren_depth = 0;

    for (let idx = 0; idx < program_lines.length; idx++) {
        let item = program_lines[idx];
        let line_num = Array.isArray(item) ? item[0] : idx + 1;
        let raw_line = Array.isArray(item) ? item[1] : item;

        let comment_idx = raw_line.indexOf('#');
        let content = comment_idx !== -1 ? raw_line.substring(0, comment_idx) : raw_line;

        if (content.trimEnd().endsWith('\\')) {
            current_line += content.substring(0, content.lastIndexOf('\\'));
            current_num = current_num || line_num;
            continue;
        }

        let content_no_strings = content.replace(/("[^"\\]*(?:\\.[^"\\]*)*"|'[^'\\]*(?:\\.[^'\\]*)*')/g, '');
        paren_depth += (content_no_strings.match(/\(/g) || []).length - (content_no_strings.match(/\)/g) || []).length;

        current_line += (current_line && paren_depth >= 0 ? " " : "") + content.trim();
        current_num = current_num || line_num;

        if (paren_depth <= 0) {
            final_merged.push([current_num, current_line.trim()]);
            current_line = "";
            current_num = null;
            paren_depth = 0;
        }
    }

    if (current_line) final_merged.push([current_num || program_lines.length, current_line.trim()]);
    return final_merged;
}

function parse_sections(program_lines) {
    let sections = [];
    let current_name = null;
    let current_lines = [];

    for (let idx = 0; idx < program_lines.length; idx++) {
        let item = program_lines[idx];
        let ln = Array.isArray(item) ? item[0] : idx + 1;
        let raw = Array.isArray(item) ? item[1] : item;
        let stripped = raw.trim();

        if (stripped.startsWith('@set.') || stripped.startsWith('@section.')) {
            let alias_name = null;
            if (stripped.includes(' as ')) {
                let parts = stripped.split(' as ');
                stripped = parts.slice(0, -1).join(' as ').trim();
                alias_name = parts[parts.length - 1].trim();
            }

            let name_part = stripped.split('at')[0];
            let addr_part = stripped.substring(name_part.length).replace(/^at/, '');

            if (current_name !== null || current_lines.length > 0) sections.push([current_name, current_lines]);
            current_name = stripped.startsWith('@set.') ? name_part.trim().substring(5) : name_part.trim().substring(9);

            if (alias_name) register_alias(alias_name, current_name);

            current_lines = [];
            if (addr_part) {
                let org_part = addr_part.split('backup')[0];
                let bkup_part = addr_part.substring(org_part.length).replace(/^backup/, '');

                org_part = org_part.trim();
                bkup_part = bkup_part.trim();

                if (org_part) current_lines.push([ln, `org ${org_part}`]);
                if (bkup_part) current_lines.push([ln, `backup ${bkup_part}`]);
            }
        } else {
            current_lines.push([ln, raw]);
        }
    }
    if (current_name !== null || current_lines.length > 0) sections.push([current_name, current_lines]);

    let named = sections.filter(s => s[0] !== null);
    let unnamed = sections.filter(s => s[0] === null);
    return named.concat(unnamed);
}

function process_line(line, program_iter = null) {
    line = line.trim();
    if (!line) return;
    if (line.startsWith('/*')) { loader.set_state('in_comment', true); return; }
    if (line.includes('*/')) { loader.set_state('in_comment', false); return; }
    if (loader.in_comment) return;

    if (line.includes(';')) {
        let cmds = line.split(';');
        for (let cmd of cmds) {
            process_line(cmd.toLowerCase(), program_iter);
        }
    } else {
        dispatch_command_handler(line, program_iter);
    }
}

function _parse_two_args(inner) {
    let paren_balance = 0;
    let split_idx = -1;
    for (let i = 0; i < inner.length; i++) {
        let c = inner[i];
        if (c === '(') paren_balance++;
        else if (c === ')') paren_balance--;
        else if (c === ',' && paren_balance === 0) {
            split_idx = i;
            break;
        }
    }

    if (split_idx === -1) {
        return [inner.trim(), "0"];
    }

    return [inner.substring(0, split_idx).trim(), inner.substring(split_idx + 1).trim()];
}

function _eval_fill_args(expr1, expr2) {
    let eval_scope = { pr_length: loader.result.length, ...loader.vars_dict };

    for (let k in loader.labels) {
        if (!(k in eval_scope)) eval_scope[k] = k; // treat as string
    }
    for (let k in loader.global_labels) {
        if (!(k in eval_scope)) eval_scope[k] = k;
    }

    eval_scope['adr'] = function (label, offset = 0) {
        if (typeof label !== 'string') throw new utils.CompilerError(`Label must be str, got ${typeof label}`);
        if (label in loader.labels) {
            return (loader.home || 0) + loader.labels[label] + offset;
        }
        if (label in loader.global_labels) {
            let sec = loader.label_sections[label];
            let sec_home = 0;
            if (sec && sec in loader.section_addresses) {
                sec_home = loader.section_addresses[sec].org || 0;
            }
            return sec_home + loader.global_labels[label] + offset;
        }
        throw new utils.CompilerError(`Label '${label}' not found (padding requires previously defined labels)`);
    };

    function prepare_expr(expr) {
        let expanded = expr.replace(/\bpr_length\b/g, String(loader.result.length));
        if (Object.keys(loader.vars_dict).length > 0) {
            let pat = new RegExp('\\b(' + Object.keys(loader.vars_dict).map(escapeRegExp).join('|') + ')\\b', 'g');
            expanded = expanded.replace(pat, (m, p1) => String(loader.vars_dict[p1]));
        }
        return expanded;
    }

    let val1 = parseInt(utils.safe_eval(prepare_expr(expr1), eval_scope));
    let val2 = parseInt(utils.safe_eval(prepare_expr(expr2), eval_scope));
    return [val1, val2];
}

function _do_fill(count, value) {
    if (count < 0) throw new utils.CompilerError(`Padding count cannot be negative: ${count}`);
    if (count === 0) return;
    let h = value.toString(16);
    if (h.length % 2 !== 0) h = '0' + h;
    let val = parseInt(h, 16);
    let byte_seq = [];
    for (let i = 0; i < Math.floor(h.length / 2); i++) {
        byte_seq.push(val & 0xFF);
        val >>= 8;
    }
    for (let i = 0; i < count; i++) {
        loader.result.push(...byte_seq);
    }
}

function handle_fill_command(line) {
    let inner = line.trim().substring(5, line.trim().length - 1).trim();
    let [expr1, expr2] = _parse_two_args(inner);
    let [count, value] = _eval_fill_args(expr1, expr2);
    _do_fill(count, value);
}

function handle_align_command(line) {
    let inner = line.trim().substring(6, line.trim().length - 1).trim();
    let [expr1, expr2] = _parse_two_args(inner);
    let [size, value] = _eval_fill_args(expr1, expr2);
    if (size <= 0) throw new utils.CompilerError(`Align size must be > 0, got ${size}`);

    let current_addr = (loader.home || 0) + loader.result.length;
    let rem = current_addr % size;
    let count = (size - rem) % size;
    _do_fill(count, value);
}

function handle_pad_command(line) {
    let is_abs = line.trim().startsWith('pad_abs');
    let inner = is_abs ? line.trim().substring(8, line.trim().length - 1).trim() : line.trim().substring(4, line.trim().length - 1).trim();
    let [expr1, expr2] = _parse_two_args(inner);
    let [target, value] = _eval_fill_args(expr1, expr2);

    let count;
    if (is_abs) {
        if (loader.home == null) throw new utils.CompilerError(`pad_abs requires section origin to be known (use @set.sec at address)`);
        let current_addr = loader.home + loader.result.length;
        count = target - current_addr;
    } else {
        count = target - loader.result.length;
    }
    _do_fill(count, value);
}

function handle_label_definition(line) {
    let line_str = line.trim();
    let label = line_str.toLowerCase().startsWith('lbl ') ? line_str.substring(4).trim().toLowerCase() : line_str.substring(0, line_str.length - 1).trim().toLowerCase();

    let at_match = label.match(/\s+at\s+(.+)$/);
    if (at_match) {
        let address_expr = at_match[1];
        let label_name = label.substring(0, at_match.index).trim();
        let address = parseInt(utils.safe_eval(address_expr));

        if (label_name in loader.labels) throw new utils.CompilerError(`Duplicate label: '${label_name}'`);

        loader.global_labels[label_name] = address;
        if (loader.is_pass1) {
            loader.label_sections[label_name] = loader.current_section_name;
        }
        if (!loader.is_pass1) {
            utils.note(`Label ${label_name} is at address ${"0x" + address.toString(16)}\n`.trim() + "(absolute) \n");
        }
        return;
    }

    if (label in loader.labels) throw new utils.CompilerError(`Duplicate label: '${label}'`);
    loader.labels[label] = loader.result.length;
}

function collect_block_body(first_line_rest, program_iter, line_num = null) {
    if (first_line_rest.includes('}')) {
        let content = first_line_rest.substring(0, first_line_rest.lastIndexOf('}')).trim();
        let items = [];
        if (content) {
            if (line_num !== null) items.push([line_num, content]);
            else items.push(content);
        }
        return [items, true];
    }

    let body_items = [];
    let depth = 1;
    if (program_iter === null) throw new utils.CompilerError(`Block requires an iterator`);

    let next = program_iter.next();
    while (!next.done) {
        let item = next.value;
        let ln = null, content = "";
        if (Array.isArray(item) && item.length === 2) {
            ln = item[0];
            content = item[1];
        } else if (typeof item === 'object' && item !== null && item.exec) {
            content = item.exec;
        } else {
            content = String(item);
        }

        let content_strip = content.trim();
        if (!content_strip) {
            next = program_iter.next();
            continue;
        }

        depth += (content_strip.match(/\{/g) || []).length - (content_strip.match(/\}/g) || []).length;
        if (depth <= 0) {
            if (content_strip.includes('}')) {
                let before_close = content_strip.substring(0, content_strip.indexOf('}')).trim();
                if (before_close) {
                    if (typeof item === 'object' && !Array.isArray(item)) {
                        let d = { ...item };
                        d.exec = before_close;
                        body_items.push(d);
                    } else {
                        body_items.push(ln !== null ? [ln, before_close] : before_close);
                    }
                }
            }
            break;
        }
        body_items.push(item);
        next = program_iter.next();
    }
    return [body_items, false];
}

function handle_function_definition(line, program_iter) {
    let m = line.trim().match(/^func\s+(\w+)\s*\((.*?)\)\s*\{/);
    if (!m) throw new utils.CompilerError(`Invalid func syntax: ${line}. Expected 'func name(args) {'`);
    let func_name = m[1];
    let args_str = m[2].trim();

    let line_num = loader.current_line_num;
    let [body_items, _] = collect_block_body(line.substring(m.index + m[0].length).trim(), program_iter, line_num);

    let body = [];
    let return_expr = null;
    for (let item of body_items) {
        let b_ln = Array.isArray(item) ? item[0] : (item.num || line_num);
        let content = Array.isArray(item) ? item[1] : (item.exec || String(item));
        let stripped = content.trim();
        if (!stripped) continue;
        if (stripped.startsWith('return ')) {
            if (return_expr !== null) throw new utils.CompilerError(`Multiple returns in ${func_name}`);
            return_expr = stripped.substring(7).trim();
        } else {
            body.push([b_ln, stripped]);
        }
    }

    if (return_expr !== null && body.length > 0) {
        throw new utils.CompilerError(`Function ${func_name} with return must ONLY contain return`);
    }

    let params = [];
    if (args_str) {
        for (let a of args_str.split(',')) {
            a = a.trim();
            if (a.includes('=')) {
                let parts = a.split('=');
                params.push([parts[0].trim(), parts.slice(1).join('=').trim()]);
            } else {
                params.push([a, null]);
            }
        }
    }

    let funcData = { params: params };
    if (return_expr !== null) funcData.return_expr = return_expr;
    else funcData.body = body;

    loader.defined_functions[func_name] = funcData;
}



function handle_repeat_command(line, program_iter) {
    let m = line.trim().match(/^(?:repeat|loop)\s+(.+?)\s*\{/);
    if (!m) throw new utils.CompilerError(`Invalid repeat syntax: ${line}. Expected 'repeat count {'`);
    let count;
    try {
        count = parseInt(utils.safe_eval(m[1].trim(), { ...loader.vars_dict }));
    } catch (e) {
        throw new utils.CompilerError(`Error eval repeat count '${m[1]}': ${e.message}`);
    }

    let line_num = loader.current_exec_info ? loader.current_exec_info.num : null;
    let [body_items, _] = collect_block_body(line.substring(m.index + m[0].length).trim(), program_iter, line_num);

    for (let i = 0; i < count; i++) {
        let b_iter = (function* () {
            for (let b of body_items) yield b;
        })();

        for (let item of body_items) {
            b_iter.next(); // advance iterator for each item processed to match python semantics if inner macros rely on it
            if (typeof item === 'object' && !Array.isArray(item)) {
                loader.set_state('current_exec_info', { line: item.exec, raw: item.raw || "", num: item.num, ctx: item.ctx || "" });
                process_line(item.exec, b_iter);
            } else if (Array.isArray(item) && item.length === 2) {
                loader.set_state('current_exec_info', { line: item[1], raw: item[1], num: item[0], ctx: "" });
                process_line(item[1], b_iter);
            } else {
                process_line(String(item), b_iter);
            }
        }
    }
}

function handle_eval_expression(line) {
    let expr = line.substring(5, line.length - 1).trim();
    expr = expr.replace(/adr\(\s*\$\s*\)/g, 'adr("$")');
    let expanded_expr = expr.replace(/\bpr_length\b/g, 'sizeof()');

    if (Object.keys(loader.vars_dict).length > 0) {
        let pat = new RegExp('\\b(' + Object.keys(loader.vars_dict).map(escapeRegExp).join('|') + ')\\b', 'g');
        expanded_expr = expanded_expr.replace(pat, (m, p1) => String(loader.vars_dict[p1]));
    }

    expanded_expr = expanded_expr.replace(/\bdist\.(\w+)\b/g, 'dist("$1")');
    expanded_expr = expanded_expr.replace(/\bsizeof\((.*?)\)/g, (m, p1) => `sizeof("${p1.trim()}")`);
    expanded_expr = expanded_expr.replace(/\bpr_org\((.*?)\)/g, (m, p1) => `pr_org("${p1.trim()}")`);
    expanded_expr = expanded_expr.replace(/\bpr_backup\((.*?)\)/g, (m, p1) => `pr_backup("${p1.trim()}")`);

    let eval_scope = { pr_length: loader.result.length, ...loader.vars_dict };

    function eval_nested(s) {
        while (s.includes('eval(')) {
            let s_old = s;
            let regex = /\beval\(([^()]*(?:\([^()]*\)[^()]*)*)\)/g;
            let matches = [...s.matchAll(regex)];
            for (let i = matches.length - 1; i >= 0; i--) {
                let m = matches[i];
                let inner = m[1].trim();
                let inner_res = eval_nested(inner);
                if (inner_res.includes('adr(')) {
                    s = s.substring(0, m.index) + `(${inner_res})` + s.substring(m.index + m[0].length);
                } else {
                    let val = utils.safe_eval(inner_res, eval_scope);
                    if (Array.isArray(val)) val = val[0];
                    s = s.substring(0, m.index) + String(val) + s.substring(m.index + m[0].length);
                }
            }
            if (s === s_old) break;
        }
        return s;
    }

    expanded_expr = eval_nested(expanded_expr);

    if (expanded_expr.includes('adr(') || expanded_expr.includes('sizeof(') || expanded_expr.includes('dist.') || expanded_expr.includes('pr_org(') || expanded_expr.includes('pr_backup(')) {
        let hexMatches = [...expanded_expr.matchAll(/\b0x([0-9a-fA-F]+)\b/g)];
        let max_len = 4;
        for (let m of hexMatches) {
            let len = m[1].length + (m[1].length % 2);
            if (len > max_len) max_len = len;
        }
        let max_bytes = Math.floor(max_len / 2);
        loader.deferred_evals.push([loader.result.length, expanded_expr, { ...loader.current_exec_info }, max_bytes]);
        for (let i = 0; i < max_bytes; i++) loader.result.push(0);
        return;
    }

    let val = utils.safe_eval(expanded_expr, eval_scope);

    if (typeof val === 'number' || Array.isArray(val)) {
        let hexMatches = [...expanded_expr.matchAll(/\b0x([0-9a-fA-F]+)\b/g)];
        let max_len = 2;
        for (let m of hexMatches) {
            let len = m[1].length + (m[1].length % 2);
            if (len > max_len) max_len = len;
        }
        let items = Array.isArray(val) ? val : [val];
        for (let item of items) {
            if (typeof item === 'number') {
                let hexStr = item.toString(16);
                while (hexStr.length < max_len) hexStr = '0' + hexStr;
                process_line(`0x${hexStr}`);
            } else {
                process_line(`"${item}"`);
            }
        }
    } else if (typeof val === 'string') {
        process_line(`"${val}"`);
    } else {
        throw new utils.CompilerError(`Unsupported eval type: ${typeof val}`);
    }
}

function handle_list_command(line, program_iter) {
    let content = line.substring(1);
    if (content.includes(']')) {
        let inner = content.substring(0, content.indexOf(']'));
        if (inner.trim()) process_line(inner);
        return;
    }

    let parts = [];
    if (content.trim()) parts.push(content.trim());

    if (program_iter) {
        let next = program_iter.next();
        while (!next.done) {
            let item = next.value;
            let s = Array.isArray(item) ? item[1].trim() : (item.exec ? item.exec.trim() : String(item).trim());
            if (!s) {
                next = program_iter.next();
                continue;
            }
            if (s.includes(']')) {
                let before = s.substring(0, s.indexOf(']')).trim();
                while (before.endsWith(';')) before = before.substring(0, before.length - 1);
                if (before) parts.push(before);
                break;
            }
            while (s.endsWith(';')) s = s.substring(0, s.length - 1);
            parts.push(s);
            next = program_iter.next();
        }
    }

    let cleaned = parts.filter(p => p);
    if (cleaned.length > 0) {
        process_line(cleaned.join(';'));
    }
}

function handle_hex_data(line) {
    if (line.startsWith('0x')) {
        let h = line.substring(2);
        if (h.length % 2 !== 0) h = '0' + h;
        let val = parseInt(h, 16);
        for (let i = 0; i < Math.floor(h.length / 2); i++) {
            loader.result.push(val & 0xFF);
            val >>= 8;
        }
    } else {
        let str = line.substring(3).replace(/\s/g, '');
        for (let i = 0; i < str.length; i += 2) {
            loader.result.push(parseInt(str.substring(i, i + 2), 16));
        }
    }
}

function handle_call_command(line) {
    let cmd = line.substring(4).trim();
    let adr, tags;
    let parsedAddr = parseInt(cmd, 16);
    if (!isNaN(parsedAddr) && /^(?:0x)?[0-9a-fA-F]+$/i.test(cmd)) {
        adr = parsedAddr;
        tags = [];
    } else {
        if (!(cmd in loader.commands)) {
            // Simplified error reporting without difflib closest match
            throw new utils.CompilerError(`Call target not found: ${cmd}`);
        }
        let commandData = loader.commands[cmd];
        adr = commandData[0];
        tags = commandData[1];
        for (let t of tags) {
            if (t.startsWith('warning')) utils.note(t + '\n');
        }
    }

    let offset = 0;
    if (!loader.gadgets_offset_applied) {
        try {
            let irange = loader.datalabels['input_range'] || loader.datalabels['input_area'];
            if (loader.home !== null && irange <= loader.home && loader.home < irange + 0xc8) {
                offset = 0x30300000;
            }
        } catch (e) {
            offset = 0x30300000;
        }
    }

    let finalAddr = (adr + offset).toString(16);
    while (finalAddr.length < 8) finalAddr = '0' + finalAddr;
    process_line(`0x${finalAddr}`);
}

function handle_goto_command(line) {
    let parts = line.split(/\s+/, 2);
    if (parts.length < 2) throw new utils.CompilerError(`Invalid goto syntax: ${line}. Expected 'goto <label>'`);
    let lbl = parts[1].toLowerCase();
    let reg = line.startsWith('goto_er6') ? 'er6' : 'er14';
    process_line(`${reg} = eval(adr("${lbl}") - 0x02);call sp=${reg},pop ${reg === 'er6' ? 'er8' : reg}`);
}

function handle_address_command(line) {
    let inner = line.trim().substring(4, line.trim().length - 1).trim();
    let parts = inner.split(',').map(p => p.trim());
    if (parts.length === 0 || !parts[0] || parts.length > 3) throw new utils.CompilerError(`Invalid adr syntax: ${line}. Expected 'adr(label, offset, base)'`);

    let expr = [`adr("${parts[0]}")`];
    if (parts.length > 1 && parts[1]) {
        expr.push(parts[1].startsWith('+') || parts[1].startsWith('-') ? parts[1] : '+' + parts[1].replace(/ /g, ''));
    }
    if (parts.length > 2 && parts[2]) {
        let base_val = parts[2].replace(/ /g, '');
        expr.push(`+ ${base_val} - homeof("${parts[0]}")`);
    }

    if (expr.length === 1) {
        loader.deferred_evals.push([loader.result.length, expr[0], { ...loader.current_exec_info }]);
        loader.result.push(0, 0);
    } else {
        process_line(`eval(${expr.join(' ')})`);
    }
}

function handle_define_gadget_command(line) {
    if (!line.includes(':')) throw new utils.CompilerError(`Invalid def syntax: ${line}. Expected 'def name: address'`);
    let parts = line.substring(3).trim().split(':');
    let cmd = utils.canonicalize(parts[0].trim()).toLowerCase();
    let addr_str = parts.slice(1).join(':').trim();

    let tags = [];
    while (cmd.startsWith('{')) {
        let end = cmd.indexOf('}');
        if (end < 0) throw new utils.CompilerError(`Unmatched "{" in inline def command: ${line}`);
        tags.push(cmd.substring(1, end));
        cmd = cmd.substring(end + 1).trim();
    }

    let addr = parseInt(addr_str, 16);
    if (isNaN(addr)) throw new utils.CompilerError(`Invalid address in def: ${addr_str}`);

    loader.add_command(loader.commands, addr, cmd, tags, 'inline def');
    utils.note(`Gadget ${cmd} is ${addr_str}\n`.trim() + "\n");
}

function handle_assignment_command(line, program_iter) {
    let parts = line.split('=');
    let l = parts[0].trim();
    let r = parts.slice(1).join('=').trim();

    let m_func = r.match(/^(\w+)\s*\(((?:[^()]+|\([^()]*\))*)\)$/);
    if (m_func && m_func[1] in loader.defined_functions) {
        let f = loader.defined_functions[m_func[1]];
        if (!("return_expr" in f)) throw new utils.CompilerError(`Func ${m_func[1]} cannot be assigned (no return)`);

        let args = [];
        let regex = /("(?:[^"\\]|\\.)*"|[^,]+)/g;
        let match;
        while ((match = regex.exec(m_func[2])) !== null) {
            args.push(match[1].trim());
        }
        if (args.length === 1 && args[0] === '' && !m_func[2]) args = [];

        if (args.length !== f.params.length) throw new utils.CompilerError(`Args mismatch in ${r}`);
        r = f.return_expr;
        for (let i = 0; i < f.params.length; i++) {
            let p = f.params[i][0];
            let a = args[i];
            let r_parts = r.split(/("[^"\\]*(?:\\.[^"\\]*)*"|'[^'\\]*(?:\\.[^'\\]*)*')/);
            for (let j = 0; j < r_parts.length; j += 2) {
                r_parts[j] = r_parts[j].replace(new RegExp(`\\b${escapeRegExp(p)}\\b`, 'g'), a);
            }
            r = r_parts.join('');
        }
    }

    if (r.startsWith('[')) {
        if (r.substring(1).includes(']')) {
            r = r.substring(1).split(']')[0];
        } else {
            let r_parts = [r.substring(1)];
            if (program_iter) {
                let next = program_iter.next();
                while (!next.done) {
                    let i = next.value;
                    let s = Array.isArray(i) ? i[1] : (i.exec || String(i));
                    if (!s) { next = program_iter.next(); continue; }
                    if (s.includes(']')) {
                        r_parts.push(s.split(']')[0]);
                        break;
                    }
                    r_parts.push(s);
                    next = program_iter.next();
                }
            }
            r = r_parts.join(';');
        }
    }

    if (l.startsWith("var ")) {
        let var_name = l.substring(4).trim();
        loader.vars_dict[var_name] = r;
        utils.note(`Variable '${var_name}' set to ${r}\n`.trim() + "\n");
    } else if (l.startsWith("reg ") || /^(?:ea|lr|(?:r|er|xr|qr)\d+)\b/.test(l)) {
        let reg = l.startsWith("reg ") ? l.substring(4).trim() : l;
        let paren_balance = 0;
        let new_right = [];
        for (let i = 0; i < r.length; i++) {
            let char = r[i];
            if (char === '(') paren_balance++;
            else if (char === ')') paren_balance--;
            new_right.push(char === ',' && paren_balance === 0 ? ';' : r[i]);
        }
        process_line(`call pop ${reg}`);
        let l1 = loader.result.length;
        process_line(new_right.join(''));
        if (loader.result.length - l1 !== loader.sizeof_register(reg)) {
            throw new utils.CompilerError(`Line ${line} source/dest target mismatches`);
        }
    } else if (l.startsWith("lbl ")) {
        process_line(l);
        process_line(r);
    } else {
        loader.vars_dict[l] = r;
        utils.note(`Variable '${l}' set to ${r}\n`.trim() + "\n");
    }
}

function handle_variable_expansion(line) {
    if (Object.keys(loader.vars_dict).length === 0) return process_line(line);

    let pat = new RegExp('\\b(' + Object.keys(loader.vars_dict).map(escapeRegExp).join('|') + ')(?:\\s*\\[(\\d+)\\])?\\b', 'g');
    let replaced = line.replace(pat, (match, v, idx) => {
        let val = String(loader.vars_dict[v]);
        if (idx !== undefined) {
            let i = parseInt(idx);
            if (val.startsWith('"') && val.endsWith('"')) {
                let inner = val.substring(1, val.length - 1);
                return (i >= 0 && i < inner.length) ? `"${inner[i]}"` : '';
            }
            if (val.includes(';')) {
                let items = val.split(';').map(x => x.trim()).filter(x => x);
                return (i >= 0 && i < items.length) ? items[i] : '';
            }
        }
        return val;
    });
    process_line(replaced);
}

function handle_string_command(line) {
    let m = line.trim().match(/"(.*)"/);
    if (!m) return;
    let text = m[1];

    function append_chars(content) {
        let replaced = content.replace(/\s/g, "~");
        for (let i = 0; i < replaced.length; i++) {
            let c = replaced[i];
            let hx = loader.char_to_hex[c];
            if (!hx) throw new utils.CompilerError(`Char '${c}' not found`);
            if (hx.length === 2) loader.result.push(parseInt(hx, 16));
            else {
                loader.result.push(parseInt(hx.substring(0, 2), 16), parseInt(hx.substring(2), 16));
            }
        }
    }

    let last_idx = 0;
    let i = 0;
    while (i < text.length) {
        if (text[i] === '{') {
            let before = text.substring(last_idx, i);
            if (before) append_chars(before);
            let depth = 1;
            let j = i + 1;
            while (j < text.length && depth > 0) {
                if (text[j] === '{') depth++;
                else if (text[j] === '}') depth--;
                j++;
            }
            let expr = text.substring(i + 1, j - 1).trim();
            if (expr) {
                if (/^[a-zA-Z_]\w*(?:\[\d+\])?$/.test(expr)) {
                    process_line(`eval(${expr})`);
                } else {
                    process_line(expr.startsWith('eval(') || expr.startsWith('calc(') ? expr : `eval(${expr})`);
                }
            }
            last_idx = j;
            i = j;
        } else {
            i++;
        }
    }
    let after = text.substring(last_idx);
    if (after) append_chars(after);
}

function handle_token_literal(line) {
    let content = line.trim().substring(1, line.trim().length - 1).replace(/ /g, "");
    let i = 0;
    while (i < content.length) {
        let found = false;
        for (let t of sorted_tokens) {
            if (content.startsWith(t, i)) {
                let hx = loader.token_to_hex[t];
                if (hx.length === 2) loader.result.push(parseInt(hx, 16));
                else loader.result.push(parseInt(hx.substring(0, 2), 16), parseInt(hx.substring(2), 16));
                i += t.length;
                found = true;
                break;
            }
        }
        if (!found) {
            let char = content[i];
            let hx = loader.token_to_hex[char];
            if (!hx) throw new utils.CompilerError(`Unknown token: ${char}`);
            if (hx.length === 2) loader.result.push(parseInt(hx, 16));
            else loader.result.push(parseInt(hx.substring(0, 2), 16), parseInt(hx.substring(2), 16));
            i++;
        }
    }
}


function handle_adr_of_hd_command(line) {
    let m = line.trim().match(/^adr_of\s*(?:\[(.*?)\]\s*)?(?:\[(.*?)\]\s*)?(\S+)$/);
    if (!m) throw new utils.CompilerError(`Invalid adr_of syntax: ${line}. Expected 'adr_of [offset] [base] label'`);
    let offset = m[1] ? m[1] : "+ 0";
    let base = m[2];
    let lbl = m[3];
    process_line(`adr(${lbl}, ${offset.trim()}${base ? ", " + base : ""})`);
}

function handle_adr_arith_hd_command(line) {
    let content = line.trim().substring(9).trim();
    content = content.replace(/\b(?:adr_arith|adr_of|adr)\b/g, '').trim();

    let pairs = [];
    let pair_regex = /(?:\[([^\]]+)\])?\s*([a-zA-Z_]\w*)/g;
    let match;
    while ((match = pair_regex.exec(content)) !== null) {
        pairs.push([match[1], match[2]]);
    }

    let ops = [];
    let op_regex = /\]\s*([+-])\s*(?:\[|\w)|(?:\s|[a-zA-Z_]\w*)\s*([+-])\s*(?:\[|[a-zA-Z_]\w*)/g;
    while ((match = op_regex.exec(content)) !== null) {
        ops.push(match[1] || match[2]);
    }

    if (pairs.length === 0 || pairs.length - 1 !== ops.length) {
        throw new utils.CompilerError(`Invalid adr_arith syntax: ${line}. Expected 'adr_arith [offset1] label1 + [offset2] label2'`);
    }

    let expr_parts = [];
    for (let i = 0; i < pairs.length; i++) {
        let off = pairs[i][0] ? pairs[i][0].trim() : null;
        let lbl = pairs[i][1];
        let op = i < ops.length ? ops[i] : '';

        let sub = !off ? `adr("${lbl}")` : (off.startsWith('+') || off.startsWith('-') ? `adr("${lbl}") ${off[0]} ${off.substring(1).trim()}` : `adr("${lbl}") + ${off}`);
        expr_parts.push(`(${sub}) ${op}`.trim());
    }
    let eval_str = expr_parts.join(' ').replace(/\s*[+-]\s*$/, '');
    process_line(`eval(${eval_str})`);
}

function handle_str_hd_command(line) {
    let content = line.trim().substring(3).trim();
    let m_var_str = content.match(/^([a-zA-Z_]\w*)\s+"([^"]*)"$/);
    if (m_var_str) {
        loader.vars_dict[m_var_str[1]] = m_var_str[2];
        return;
    }

    let val = null;
    let m_quote = content.match(/^"([^"]*)"$/);
    if (m_quote) {
        val = m_quote[1];
    } else {
        let m_var = content.match(/^([a-zA-Z_]\w*)$/);
        if (m_var && m_var[1] in loader.vars_dict) {
            val = String(loader.vars_dict[m_var[1]]);
        }
    }

    if (val === null) throw new utils.CompilerError(`Invalid str syntax: ${line}. Expected 'str "string"' or 'str var'`);

    let replaced = val.replace(/\s/g, "~");
    for (let i = 0; i < replaced.length; i++) {
        let hx = loader.char_to_hex[replaced[i]];
        if (!hx) throw new utils.CompilerError(`Char '${replaced[i]}' not found`);
        if (hx.length === 2) loader.result.push(parseInt(hx, 16));
        else loader.result.push(parseInt(hx.substring(0, 2), 16), parseInt(hx.substring(2), 16));
    }
}

function dispatch_command_handler(line, program_iter = null) {
    let ls = line.trim();
    if (ls.startsWith('org')) {
        let new_home = parseInt(utils.safe_eval(ls.substring(3))) - loader.result.length;
        if (loader.home !== null && loader.home !== new_home) throw new utils.CompilerError(`Inconsistent value of \`home\``);
        loader.set_state('home', new_home);
    } else if (ls.startsWith('backup ')) {
        loader.set_state('backup_address', parseInt(utils.safe_eval(ls.substring(7))));
    } else if (ls.startsWith('"')) {
        handle_string_command(ls);
    } else if (ls.startsWith("'")) {
        handle_token_literal(ls);
    } else if (ls.startsWith('0x') || (ls.startsWith('hex') && !ls.includes('hex_'))) {
        if (ls.startsWith('0x') && !/^0x[0-9a-fA-F]+$/.test(ls)) handle_eval_expression(`eval(${ls})`);
        else handle_hex_data(ls);
    } else if (ls in loader.datalabels) {
        process_line(`0x${loader.datalabels[ls].toString(16)}`);
    } else if (ls in loader.commands) {
        process_line('call ' + ls);
    } else if (ls.startsWith('call')) {
        handle_call_command(ls);
    } else if (ls.startsWith('def') || ls.startsWith('@def')) {
        handle_define_gadget_command(ls);
    } else if (ls.includes('=')) {
        handle_assignment_command(ls, program_iter);
    } else if ((ls.toLowerCase().startsWith('lbl ') || ls.includes(":")) && !ls.includes('def') && !ls.includes('"')) {
        handle_label_definition(ls);
    } else if (ls.startsWith("func")) {
        handle_function_definition(ls, program_iter);
    } else if ((ls.startsWith("repeat") || ls.startsWith("loop")) && !ls.startsWith('loop_')) {
        handle_repeat_command(ls, program_iter);
    } else if ((ls.startsWith('eval(') || ls.startsWith('calc(')) && ls.endsWith(')')) {
        handle_eval_expression(ls);
    } else if (ls.startsWith('fill(') && ls.endsWith(')')) {
        handle_fill_command(ls);
    } else if (ls.startsWith('align(') && ls.endsWith(')')) {
        handle_align_command(ls);
    } else if ((ls.startsWith('pad(') || ls.startsWith('pad_abs(')) && ls.endsWith(')')) {
        handle_pad_command(ls);
    } else if (ls.startsWith('goto') || ls.startsWith('goto_er14') || ls.startsWith('goto_er6')) {
        handle_goto_command(ls);
    } else if (ls.toLowerCase().startsWith('adr(')) {
        handle_address_command(ls);
    } else if (/^\w+(\[\d+\])?$/.test(ls) && ls.match(/^\w+/)[0] in loader.vars_dict) {
        handle_variable_expansion(ls);
    } else if (ls.startsWith('pr_length')) {
        loader.sizeof_cmds.push([loader.result.length, loader.current_section_name, { ...loader.current_exec_info }]);
        loader.result.push(0, 0);
    } else if (ls.startsWith('sizeof(') || ls === 'sizeof()') {
        let m = ls.match(/^sizeof\((.*?)\)$/);
        loader.sizeof_cmds.push([loader.result.length, m && m[1].trim() ? m[1].trim() : loader.current_section_name, { ...loader.current_exec_info }]);
        loader.result.push(0, 0);
    } else if (ls.startsWith('adr_of')) {
        handle_adr_of_hd_command(ls);
    } else if (ls.startsWith('adr_arith')) {
        handle_adr_arith_hd_command(ls);
    } else if (ls.startsWith('str')) {
        handle_str_hd_command(ls);
    } else if (ls.startsWith('[')) {
        handle_list_command(ls, program_iter);
    } else {
        utils.check_keyword(ls.split(/\s+/)[0]);
        throw new utils.CompilerError(`Unrecognized command: ${ls.split(/\s+/)[0]}`);
    }
}

export {
    init_handlers, register_alias, run_alias, add_macro, run_macro, run_func,
    split_lines, merge_lines, parse_sections, process_line, dispatch_command_handler, handle_function_definition
};
