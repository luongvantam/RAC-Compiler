import * as utils from './utils.js';
import * as loader from './loader.js';
import * as handlers from './handlers.js';

function build_env() {
    let env = {};
    for (let [k, v] of Object.entries(loader.vars_dict)) {
        env[k] = Array.isArray(v) ? (v[0] | (v[1] << 8)) : v; // Simplified array to int conversion for little endian
    }

    function adr_eval(label, offset = 0) {
        if (typeof label === 'number') return utils.createAdrInt(label + offset);
        if (typeof label !== 'string') throw new utils.CompilerError(`Label must be str, got ${typeof label}`);
        let val;
        if (label === '$') val = (loader.current_pos || 0) + (loader.home || 0) + offset;
        else if (label in loader.labels) val = (loader.home || 0) + loader.labels[label] + offset;
        else if (label in loader.global_labels) val = loader.global_labels[label] + offset;
        else if (loader.is_pass1) val = 0;
        else throw new utils.CompilerError(`Label not found: ${label}`);
        return utils.createAdrInt(val);
    }

    function sizeof_eval(sec_name = "") {
        if (!sec_name || sec_name === loader.current_section_name) return loader.result.length;
        if (sec_name in loader.section_addresses) return loader.section_addresses[sec_name].length || 0;
        if (loader.is_pass1) return 0;
        throw new utils.CompilerError(`Section '${sec_name}' not found for sizeof calculation`);
    }

    function dist_eval(sec_name) {
        let sec = loader.section_addresses[sec_name] || {};
        let org = sec.org;
        let backup = sec.backup;
        if (sec_name === loader.current_section_name) {
            org = loader.home;
            backup = loader.backup_address;
        }
        if (org !== undefined && backup !== undefined && org !== null && backup !== null) {
            return Math.abs(backup - org) & 0xFFFF;
        }
        if (loader.is_pass1) return 0;
        throw new utils.CompilerError(`Section '${sec_name}' dist information missing`);
    }

    function homeof_eval(label) {
        if (typeof label === 'number') label = String(label);
        if (label in loader.labels) return loader.home || 0;
        if (label in loader.global_labels) {
            let sec = loader.label_sections[label];
            if (sec && sec in loader.section_addresses) {
                return loader.section_addresses[sec].org || 0;
            }
            return 0;
        }
        if (loader.is_pass1) return 0;
        throw new utils.CompilerError(`Home of label '${label}' not found`);
    }

    function pr_org_eval(sec_name = "") {
        let sec = loader.section_addresses[sec_name] || {};
        let org = sec.org;
        if (!sec_name || sec_name === loader.current_section_name) org = loader.home;
        if (org !== undefined && org !== null) return org & 0xFFFF;
        if (loader.is_pass1) return 0;
        throw new utils.CompilerError(`Section '${sec_name}' org information missing`);
    }

    function pr_backup_eval(sec_name = "") {
        let sec = loader.section_addresses[sec_name] || {};
        let backup = sec.backup;
        if (!sec_name || sec_name === loader.current_section_name) backup = loader.backup_address;
        if (backup !== undefined && backup !== null) return backup & 0xFFFF;
        if (loader.is_pass1) return 0;
        throw new utils.CompilerError(`Section '${sec_name}' backup information missing`);
    }

    for (let k in loader.labels) {
        if (!(k in env)) env[k] = adr_eval(k);
    }
    for (let k in loader.global_labels) {
        if (!(k in env)) env[k] = utils.createAdrInt(loader.global_labels[k]);
    }

    env['adr'] = adr_eval;
    env['sizeof'] = sizeof_eval;
    env['dist'] = dist_eval;
    env['homeof'] = homeof_eval;
    env['pr_org'] = pr_org_eval;
    env['pr_backup'] = pr_backup_eval;

    return env;
}

function eval_all() {
    let env = build_env();
    let home_deps = [];
    let temp_deferred = [...loader.deferred_evals];
    loader.deferred_evals.length = 0;
    loader.subscript_deps.length = 0;

    for (let req of temp_deferred) {
        let pos = req[0], expr = req[1], exec_info = req[2], max_bytes = 2;
        if (req.length === 4) max_bytes = req[3];

        loader.set_state('current_pos', pos);
        loader.set_state('current_exec_info', exec_info);

        let val, mult = 0;
        try {
            val = utils.safe_eval(expr, env);

            if (expr.includes('[') || loader.home !== null) {
                mult = 0;
                if (loader.home === null) {
                    loader.subscript_deps.push([pos, expr, exec_info, max_bytes]);
                }
            } else {
                let env_1m = build_env();
                let o_adr = env_1m['adr'], o_pr_org = env_1m['pr_org'], o_homeof = env_1m['homeof'];

                env_1m['adr'] = (l, o = 0) => o_adr(l, o) + ((l === '$' || l in loader.labels || (typeof l === 'string' && l in loader.global_labels)) ? 1000000 : 0);
                env_1m['pr_org'] = (s = "") => o_pr_org(s) + ((!s || s === loader.current_section_name) ? 1000000 : 0);
                env_1m['homeof'] = (l) => o_homeof(l) + ((l in loader.labels || (typeof l === 'string' && l in loader.global_labels)) ? 1000000 : 0);

                let val_1m = utils.safe_eval(expr, env_1m);
                mult = Math.floor((val_1m - val) / 1000000);
            }
        } catch (e) {
            try {
                let temp_env = {};
                for (let [k, v] of Object.entries(env)) {
                    if (typeof v === 'string' && v.startsWith("eval(")) {
                        temp_env[k] = utils.safe_eval(v.substring(5, v.length - 1), env);
                    } else {
                        temp_env[k] = v;
                    }
                }
                val = utils.safe_eval(expr, temp_env);
                mult = 0;
            } catch (e2) {
                throw new utils.CompilerError(`Deferred eval error in ${expr}: ${e2.message}`);
            }
        }

        if (typeof val !== 'number') throw new utils.CompilerError(`Eval ${expr} not integer`);

        if (mult === 0) {
            val &= (1 << (max_bytes * 8)) - 1;
            let overwrite = false;
            for (let i = 0; i < max_bytes; i++) if (loader.result[pos + i] !== 0) overwrite = true;
            if (!loader.is_pass1 && overwrite) {
                utils.note(`[WARN] eval_abs overwrite at ${"0x" + pos.toString(16).padStart(4, "0").toUpperCase()}` + '\n');
            }
            for (let i = 0; i < max_bytes; i++) {
                loader.result[pos + i] = (val >> (8 * i)) & 0xFF;
            }
        } else {
            home_deps.push([pos, val, mult, max_bytes]);
        }
    }
    return home_deps;
}

function configure_memory_layout(base_sp, addr_resolution_list, dependencies) {
    if (loader.home === null) {
        loader.set_state('home', base_sp - (loader.labels['home'] || 0));
        if (!loader.is_pass1 && loader.current_section_name === null) {
            let max_size = 0x8E00 - loader.home;
            let current_size = loader.result.length;
            if (current_size > max_size) {
                utils.note(`[WARN] Total length after home = ${current_size} bytes > ${max_size} bytes\n`.trim() + '\n');
            }
        }
    }

    if (loader.subscript_deps && loader.subscript_deps.length > 0) {
        let env_now = build_env();
        for (let [pos, expr, exec_info, max_bytes] of loader.subscript_deps) {
            loader.set_state('current_pos', pos);
            loader.set_state('current_exec_info', exec_info);
            try {
                let val = utils.safe_eval(expr, env_now);
                val &= (1 << (max_bytes * 8)) - 1;
                for (let i = 0; i < max_bytes; i++) {
                    loader.result[pos + i] = (val >> (8 * i)) & 0xFF;
                }
            } catch (e) { }
        }
        loader.subscript_deps.length = 0;
    }

    let is_final_pass = !loader.is_pass1;
    let all_memory_requests = addr_resolution_list.concat(dependencies);

    for (let req of all_memory_requests) {
        let index, off, mult, max_bytes = 2, target;
        if (req.length === 4) {
            [index, off, mult, max_bytes] = req;
            target = off + mult * loader.home;
        } else if (req.length === 3) {
            [index, off, mult] = req;
            target = off + mult * loader.home;
        } else {
            [index, off] = req;
            target = loader.home + off;
        }

        let overwrite = false;
        for (let i = 0; i < max_bytes; i++) if (loader.result[index + i] !== 0) overwrite = true;
        if (is_final_pass && overwrite) {
            utils.note(`[WARN] Memory overwrite at ${"0x" + index.toString(16)} -> ${"0x" + target.toString(16)}\n`.trim() + '\n');
        }

        for (let i = 0; i < max_bytes; i++) {
            loader.result[index + i] = (target >> (8 * i)) & 0xFF;
        }
    }

    for (let sym_name in loader.labels) {
        let sym_offset = loader.labels[sym_name];
        let abs_addr = loader.home + sym_offset;
        loader.global_labels[sym_name] = abs_addr;
        loader.label_sections[sym_name] = loader.current_section_name;

        if (is_final_pass) {
            utils.note(`Label ${sym_name} is at address ${"0x" + abs_addr.toString(16)}\n`.trim() + '\n');
        }
    }

    if (loader.current_section_name) {
        loader.section_addresses[loader.current_section_name] = {
            org: loader.home,
            backup: loader.backup_address,
            length: loader.result.length
        };
    }

    for (let req of loader.dist_cmds) {
        let index = req[0], sec_key = req[1], exec_ctx = req[2];
        loader.set_state('current_exec_info', exec_ctx);

        let sec_data = loader.section_addresses[sec_key];
        if (!sec_data || sec_data.backup === undefined || sec_data.backup === null) {
            if (!is_final_pass) continue;
            throw new utils.CompilerError(`Missing section reference '${sec_key}'`);
        }

        let delta = Math.abs(sec_data.backup - sec_data.org) & 0xFFFF;

        if (is_final_pass && (loader.result[index] !== 0 || loader.result[index + 1] !== 0)) {
            utils.note(`[WARN] delta clash at ${"0x" + index.toString(16).padStart(4, "0").toUpperCase()}` + '\n');
        }

        loader.result[index] = delta & 0xFF;
        loader.result[index + 1] = delta >> 8;
    }
}

function finish_math() {
    for (let req of loader.relocation_expressions) {
        let pos = req[0], l_off = req[1], l_lbl = req[2], r_off = req[3], r_lbl = req[4], op = req[5];
        let l_valid = (l_lbl in loader.labels) || (l_lbl in loader.global_labels);
        let r_valid = (r_lbl in loader.labels) || (r_lbl in loader.global_labels);
        if (!l_valid || !r_valid) {
            if (loader.is_pass1) continue;
            throw new utils.CompilerError(`Label not found in adr: ${l_lbl}, ${r_lbl}`);
        }
        let l_addr = (l_lbl in loader.labels) ? (loader.home || 0) + loader.labels[l_lbl] : loader.global_labels[l_lbl];
        let r_addr = (r_lbl in loader.labels) ? (loader.home || 0) + loader.labels[r_lbl] : loader.global_labels[r_lbl];
        let res = (op === '+')
            ? (l_addr + l_off + r_addr + r_off)
            : (l_addr + l_off - r_addr - r_off);
        res &= 0xFFFF;
        if (!loader.is_pass1 && (loader.result[pos] !== 0 || loader.result[pos + 1] !== 0)) {
            utils.note(`[WARN] adr overwrite at ${"0x" + pos.toString(16).padStart(4, "0").toUpperCase()}` + '\n');
        }
        loader.result[pos] = res & 0xFF;
        loader.result[pos + 1] = res >> 8;
    }

    for (let req of loader.sizeof_cmds) {
        let pos = req[0], sec = req[1], exec_info = req[2];
        loader.set_state('current_exec_info', exec_info);
        let val = null;
        if (!sec || sec === loader.current_section_name) val = loader.result.length;
        else if (sec in loader.section_addresses) val = loader.section_addresses[sec].length || 0;
        else if (loader.is_pass1) val = 0;

        if (val === null) throw new utils.CompilerError(`Section '${sec}' not found for sizeof calculation`);
        if (!loader.is_pass1 && (loader.result[pos] !== 0 || loader.result[pos + 1] !== 0)) {
            utils.note(`[WARN] sizeof overwrite at ${"0x" + pos.toString(16).padStart(4, "0").toUpperCase()}` + '\n');
        }
        loader.result[pos] = val & 0xFF;
        loader.result[pos + 1] = val >> 8;
    }

    for (let req of loader.pr_org_cmds) {
        let pos = req[0], sec = req[1], exec_info = req[2];
        loader.set_state('current_exec_info', exec_info);
        let val = null;
        if (!sec || sec === loader.current_section_name) val = loader.home;
        else if (sec in loader.section_addresses) val = loader.section_addresses[sec].org;
        else if (loader.is_pass1) val = 0;

        if (val === null || val === undefined) throw new utils.CompilerError(`Section '${sec}' not found for pr_org calculation`);
        if (!loader.is_pass1 && (loader.result[pos] !== 0 || loader.result[pos + 1] !== 0)) {
            utils.note(`[WARN] pr_org overwrite at ${"0x" + pos.toString(16).padStart(4, "0").toUpperCase()}` + '\n');
        }
        loader.result[pos] = val & 0xFF;
        loader.result[pos + 1] = (val >> 8) & 0xFF;
    }

    for (let req of loader.pr_backup_cmds) {
        let pos = req[0], sec = req[1], exec_info = req[2];
        loader.set_state('current_exec_info', exec_info);
        let val = null;
        if (!sec || sec === loader.current_section_name) val = loader.backup_address;
        else if (sec in loader.section_addresses) val = loader.section_addresses[sec].backup;
        else if (loader.is_pass1) val = 0;

        if (val === null || val === undefined) throw new utils.CompilerError(`Section '${sec}' not found for pr_backup calculation`);
        if (!loader.is_pass1 && (loader.result[pos] !== 0 || loader.result[pos + 1] !== 0)) {
            utils.note(`[WARN] pr_backup overwrite at ${"0x" + pos.toString(16).padStart(4, "0").toUpperCase()}` + '\n');
        }
        loader.result[pos] = val & 0xFF;
        loader.result[pos + 1] = (val >> 8) & 0xFF;
    }

    loader.relocation_expressions.length = 0;
    loader.sizeof_cmds.length = 0;
    loader.pr_org_cmds.length = 0;
    loader.pr_backup_cmds.length = 0;
}

function run_lines(program_lines, overflow_initial_sp) {
    loader.result.length = 0;
    for (let k in loader.labels) delete loader.labels[k];
    loader.address_requests.length = 0;
    loader.relocation_expressions.length = 0;
    loader.deferred_evals.length = 0;
    loader.dist_cmds.length = 0;
    loader.pr_org_cmds.length = 0;
    loader.pr_backup_cmds.length = 0;
    if (loader.subscript_deps) loader.subscript_deps.length = 0;
    loader.set_state('home', null);
    loader.set_state('backup_address', null);
    loader.set_state('in_comment', false);
    for (let k in loader.defined_functions) delete loader.defined_functions[k];
    loader.dynamic_macros.length = 0;

    let merged_lines = handlers.merge_lines(program_lines);
    let remaining_lines = [];
    for (let ln_ml of merged_lines) {
        let ln = ln_ml[0];
        let ml = ln_ml[1];
        let pts = handlers.split_lines(ml);
        for (let pt of pts) remaining_lines.push([ln, pt]);
    }

    let final_lines = [];

    while (remaining_lines.length > 0) {
        let item = remaining_lines.shift();
        let line_num = item[0];
        let raw_line = item[1];

        loader.set_state('current_line_num', line_num);
        let line_strip = utils.canonicalize(utils.del_inline_comment(raw_line)).trim();
        if (!line_strip) continue;

        if (line_strip.startsWith("def") && line_strip.includes("=>")) {
            let parts = raw_line.split('=>');
            let pat = parts[0];
            let rest = parts.slice(1).join('=>');
            let clean_pat = pat.trim().startsWith("def ") ? pat.substring(4).trim() : pat.trim().substring(3).trim();

            // program_iter concept: in JS we create an iterator from remaining_lines
            let iter = (function* () {
                while (remaining_lines.length > 0) yield remaining_lines.shift();
            })();
            handlers.add_macro(clean_pat, rest.trim(), iter);
            continue;
        }

        if (handlers.run_macro(line_strip, line_num, remaining_lines)) continue;

        let m_alias = line_strip.match(/^(.+?)\s+as\s+([a-zA-Z_]\w*)$/);
        if (m_alias && !line_strip.startsWith('"') && !line_strip.startsWith("'")) {
            handlers.register_alias(m_alias[2], m_alias[1].trim());
            continue;
        }

        raw_line = handlers.run_alias(raw_line);
        let line = utils.canonicalize(utils.del_inline_comment(raw_line));

        if (line.trim().startsWith('@set.') || line.trim().startsWith('@section.')) {
            let base_name = line.includes(' as ') ? line.substring(0, line.lastIndexOf(' as ')) : line;
            loader.set_state('current_section_name', base_name.split(/\s+/)[0].split('.')[1]);
            continue;
        }

        if (line.trim().startsWith("func ")) {
            let iter = (function* () {
                while (remaining_lines.length > 0) yield remaining_lines.shift();
            })();
            handlers.handle_function_definition(line, iter);
            continue;
        }

        if (handlers.run_func(line.trim(), raw_line, line_num, final_lines)) continue;
        final_lines.push({ exec: line, raw: raw_line, num: line_num, ctx: "" });
    }

    let i = 0;
    while (i < final_lines.length) {
        let item = final_lines[i++];
        let l, raw, ln, ctx;
        if (typeof item === 'object' && item !== null) {
            l = item.exec; raw = item.raw; ln = item.num; ctx = item.ctx || "";
        } else {
            l = item; raw = item; ln = "?"; ctx = "";
        }

        let line_to_process = utils.canonicalize(utils.del_inline_comment(handlers.run_alias(l))).trim();
        if (!line_to_process) continue;

        if (!line_to_process.startsWith('"')) {
            let result_chars = [];
            let in_str = false;
            for (let ch of line_to_process) {
                if (ch === '"') {
                    in_str = !in_str;
                    result_chars.push(ch);
                } else if (in_str) {
                    result_chars.push(ch);
                } else {
                    result_chars.push(ch.toLowerCase());
                }
            }
            line_to_process = result_chars.join('');
        }

        let note_log = '';
        let orig_note = utils._default_diagnostics.note;
        utils._default_diagnostics.note = function (st) { note_log += st; };

        loader.set_state('current_exec_info', { line: line_to_process, raw: raw, num: ln, ctx: ctx });
        try {
            let iter = (function* () {
                while (i < final_lines.length) yield final_lines[i++];
            })();
            handlers.process_line(line_to_process, iter);
        } catch (e) {
            utils._default_diagnostics.note = orig_note;
            utils.report_error(e, null, loader.current_exec_info, false); // No file name, non-fatal
        }

        utils._default_diagnostics.note = orig_note;
        if (note_log && !loader.is_pass1) {
            utils.note(note_log);
        }
    }

    try {
        let home_deps = eval_all();
        finish_math();

        let resolved_adr = [];
        for (let req of loader.address_requests) {
            let s_adr, offset, target, exec_info;
            if (req.length === 4) {
                [s_adr, offset, target, exec_info] = req;
                loader.set_state('current_exec_info', exec_info);
            } else {
                [s_adr, offset, target] = req;
            }

            if (target in loader.labels) {
                resolved_adr.push([s_adr, loader.labels[target] + offset]);
            } else if (target in loader.global_labels) {
                resolved_adr.push([s_adr, loader.global_labels[target] - loader.home + offset]);
            } else if (loader.is_pass1) {
                resolved_adr.push([s_adr, 0]);
            } else {
                throw new utils.CompilerError(`Label not found: ${target}`);
            }
        }
        loader.address_requests.length = 0;

        configure_memory_layout(overflow_initial_sp, resolved_adr, home_deps);
    } catch (e) {
        utils.report_error(e, null, loader.current_exec_info, true);
    }

    if (loader.is_pass1 || (loader.home === (loader.home + loader.result.length) && loader.current_section_name === null)) {
        return [null, null];
    }

    let notes = utils.get_notes();

    let start = "0x" + loader.home.toString(16).padStart(4, '0');
    let end = "0x" + (loader.home + loader.result.length).toString(16).padStart(4, '0');
    let backup = loader.backup_address !== null ? ` (0x${loader.backup_address.toString(16).padStart(4, '0')} -> 0x${(loader.backup_address + loader.result.length).toString(16).padStart(4, '0')})` : '';
    let section_info = `=== ${start} -> ${end}${backup} ===`;

    let result_hex = loader.result.map(b => b.toString(16).padStart(2, '0'));
    let result_lines = [];
    for (let i = 0; i < result_hex.length; i += 16) {
        result_lines.push(result_hex.slice(i, i + 16).join(' '));
    }
    let result_bytes = result_lines.join('\n');

    let full_output = `${section_info}\n${result_bytes}\n======\n`;

    return [loader.home, loader.result, notes, full_output];
}

function process_program(program_lines, overflow_initial_sp) {
    for (let k in loader.global_labels) delete loader.global_labels[k];
    for (let k in loader.section_addresses) delete loader.section_addresses[k];
    for (let k in loader.label_sections) delete loader.label_sections[k];
    for (let k in loader.aliases) delete loader.aliases[k];
    loader.set_state('aliases_pattern', null);

    let sections = handlers.parse_sections(program_lines);
    let all_notes = "";
    let main_output = "";

    if (sections.length === 1) {
        loader.set_state('is_pass1', false);
        loader.set_state('current_section_name', sections[0][0]);
        let [out_addr, out_bytes, notes, out_str] = run_lines(sections[0][1], overflow_initial_sp);
        utils.check_errors();
        if (notes) all_notes += notes;
        if (out_str) main_output += out_str;
        return {
            results: out_addr !== null ? [[loader.current_section_name, out_addr, out_bytes]] : [],
            notifications: all_notes.split('\n').filter(l => l.trim() !== ""),
            output: main_output.trim()
        };
    }

    loader.set_state('is_pass1', true);
    for (let section of sections) {
        loader.set_state('current_section_name', section[0]);
        run_lines(section[1], overflow_initial_sp);
    }

    utils.check_errors();

    loader.set_state('is_pass1', false);
    let results = [];

    for (let section of sections) {
        loader.set_state('current_section_name', section[0]);
        if (section[0] !== null) {
            main_output += `\n=== section @${section[0]} ===\n`;
        }
        let [out_addr, out_bytes, notes, out_str] = run_lines(section[1], overflow_initial_sp);
        if (notes) all_notes += notes;
        if (out_str) main_output += out_str;
        if (out_addr !== null) {
            results.push([section[0], out_addr, out_bytes]);
        }
    }

    utils.check_errors();
    loader.set_state('current_section_name', null);

    return {
        results: results,
        notifications: all_notes.split('\n').filter(l => l.trim() !== ""),
        output: main_output.trim()
    };
}

export { process_program, run_lines };
