import { CompilerError, note, canonicalize, del_inline_comment } from './utils.js';

let commands = {};
let datalabels = {};
let labels = {};
let vars_dict = {};
let disasm = {};
let char_to_hex = {};
let token_to_hex = {};

let home = null;
let current_section_name = null;
let in_comment = false;
let is_pass1 = false;
let current_exec_info = null;
let current_pos = 0;
let current_line_num = null;

let result = [];
let address_requests = [];
let relocation_expressions = [];
let sizeof_cmds = [];
let deferred_evals = [];
let pr_org_cmds = [];
let pr_backup_cmds = [];
let dist_cmds = [];
let backup_address = null;

let global_labels = {};
let section_addresses = {};
let label_sections = {};
let aliases = {};
let aliases_pattern = null;
let defined_functions = {};
let dynamic_macros = [];
let gadgets_offset_applied = false;

function add_command(command_dict, address, command, tags, debug_info = '') {
    if (!command || typeof command_dict !== 'object') {
        throw new CompilerError(`Empty command/dict ${debug_info}`);
    }
    if (command.startsWith('0x') || command.startsWith('call') || command.startsWith('goto')) {
        throw new CompilerError(`Command starts with disallowed ${command}`);
    }
    if (command.endsWith(':') || command.includes(';')) {
        throw new CompilerError(`Invalid command syntax ${debug_info}`);
    }
    if (command in command_dict) {
        let existing = command_dict[command];
        if (existing[0] === address && JSON.stringify(existing[1]) === JSON.stringify(tags)) {
            return;
        }
        throw new CompilerError(`Command ${command} appears twice ${debug_info}`);
    }
    command_dict[command] = [address, tags];
}

function parse_commands(gadgets_content, labels_content) {
    // We expect the file contents as strings instead of filenames
    commands = {};
    datalabels = {};

    let raw = gadgets_content.replace(/\/\*[\s\S]*?\*\//g, '');
    let gadget_lines = raw.split('\n');
    for (let i = 0; i < gadget_lines.length; i++) {
        let line = del_inline_comment(gadget_lines[i]).trim();
        if (!line) continue;

        let m = line.match(/^([0-9a-fA-F]+)\s+(.+)$/);
        if (m) {
            let addr = parseInt(m[1], 16);
            let cmd_raw = canonicalize(m[2]).toLowerCase();
            let tags = [];
            while (cmd_raw.startsWith('{')) {
                let end = cmd_raw.indexOf('}');
                if (end !== -1) {
                    tags.push(cmd_raw.substring(1, end));
                    cmd_raw = cmd_raw.substring(end + 1).trim();
                } else break;
            }
            let subs = cmd_raw.split(';').map(c => c.trim()).filter(c => c);
            for (let sub of subs) {
                add_command(commands, addr, canonicalize(sub).toLowerCase(), tags, `at gadgets line ${i + 1}`);
            }
        }
    }

    let label_lines = labels_content.split('\n');
    let last_global = null;
    for (let i = 0; i < label_lines.length; i++) {
        let line = label_lines[i];
        let m = line.match(/^\s*([\w_.]+)\s+(.+)$/);
        if (!m) continue;

        let raw_name = m[1];
        let reals = del_inline_comment(m[2]).split(';').map(r => r.trim()).filter(r => r && !r.startsWith('.'));
        if (reals.length === 0) continue;

        let d_match = raw_name.match(/^d_([0-9a-fA-F]+)$/);
        if (d_match) {
            for (let r of reals) {
                datalabels[r] = parseInt(d_match[1], 16);
            }
            continue;
        }

        let addr = null;
        if (/^[0-9a-fA-F]+$/.test(raw_name)) {
            addr = parseInt(raw_name, 16);
            last_global = null;
        } else {
            let g_match = raw_name.match(/^f_([0-9a-fA-F]+)/);
            if (g_match) {
                addr = parseInt(g_match[1], 16);
                if (g_match[0].length === raw_name.length) {
                    last_global = addr;
                } else {
                    let suffix = raw_name.substring(g_match[0].length);
                    let l_match = suffix.match(/^\.l_([0-9a-fA-F]+)$/);
                    if (l_match) {
                        addr += parseInt(l_match[1], 16);
                    }
                }
            } else {
                let l_match = raw_name.match(/^\.l_([0-9a-fA-F]+)$/);
                if (l_match && last_global !== null) {
                    addr = last_global + parseInt(l_match[1], 16);
                }
            }
        }

        if (addr !== null) {
            let tags = [];
            let dis = disasm[addr] || '';
            if (dis.startsWith('push lr')) {
                tags = ['del lr'];
                addr += 2;
            } else {
                tags = ['rt'];
                let a1 = addr + 2;
                while (a1 <= 0x3ffff) {
                    let d = disasm[a1] || '';
                    if (d.startsWith('push lr') || d.startsWith('pop pc') || d.startsWith('rt')) {
                        break;
                    }
                    a1 += 2;
                }
                if (!(disasm[a1] || '').startsWith('rt')) {
                    tags.push('del lr');
                }
            }

            for (let r of reals) {
                if (!(r in commands) || !commands[r][1].includes('override rename list')) {
                    if (r in commands && commands[r][0] === addr && JSON.stringify(commands[r][1]) === JSON.stringify(tags)) {
                        note(`Warning: Duplicated command ${r}\n`);
                        continue;
                    }
                    add_command(commands, addr, r, tags, `at labels line ${i + 1}`);
                }
            }
        }
    }
}

function parse_disassembly(disasm_content) {
    disasm = {};
    let lines = disasm_content.split('\n');
    for (let line of lines) {
        if (line.startsWith('\t') && line.includes(';')) {
            let p = line.split(';', 2);
            if (p[1].includes('|')) {
                let addrStr = p[1].split('|', 2)[0].trim();
                let addr = parseInt(addrStr, 16);
                disasm[addr] = p[0].trim();
            }
        }
    }
}

let subscript_deps = [];

function sizeof_register(reg_name) {
    const map = {
        'r': 2,
        'e': 2,
        'x': 4,
        'q': 8,
        'l': 4
    };
    return map[reg_name[0]] || 0;
}


function set_state(key, value) {
    if (key === 'home') home = value;
    if (key === 'current_section_name') current_section_name = value;
    if (key === 'in_comment') in_comment = value;
    if (key === 'is_pass1') is_pass1 = value;
    if (key === 'current_exec_info') current_exec_info = value;
    if (key === 'current_pos') current_pos = value;
    if (key === 'current_line_num') current_line_num = value;
    if (key === 'backup_address') backup_address = value;
    if (key === 'aliases_pattern') aliases_pattern = value;
    if (key === 'subscript_deps') subscript_deps = value;
}

export {
    set_state,
    commands, datalabels, labels, vars_dict, disasm, char_to_hex, token_to_hex,
    home, current_section_name, in_comment, is_pass1, current_exec_info, current_pos, current_line_num,
    result, address_requests, relocation_expressions, sizeof_cmds, deferred_evals, pr_org_cmds, pr_backup_cmds, dist_cmds, subscript_deps, backup_address,
    global_labels, section_addresses, label_sections, aliases, aliases_pattern, defined_functions, dynamic_macros, gadgets_offset_applied,
    add_command, parse_commands, parse_disassembly, sizeof_register
};
