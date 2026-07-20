import { report_error } from './utils.js';

function parse_extensions(extensions_content) {
    if (!extensions_content) {
        return [];
    }

    let matches = [];
    let regex = /---syntax---\s*([\s\S]*?)\s*---output---\s*([\s\S]*?)\s*---(?:\n|$)/g;
    let match;
    
    while ((match = regex.exec(extensions_content)) !== null) {
        let syntax = match[1].trim();
        let output = match[2].trim().split('\n').map(ln => ln.trim()).filter(ln => ln);
        
        let compiled_pattern_str = syntax.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&') // escape regex
                                         .replace(/\\\{/g, '(?<')
                                         .replace(/\\\}/g, '>.+?)');
        
        matches.push({
            syntax: syntax,
            output: output,
            compiled_pattern: new RegExp(`^${compiled_pattern_str}$`),
            search_pattern: new RegExp(compiled_pattern_str)
        });
    }
    
    return matches.sort((a, b) => b.syntax.length - a.syntax.length);
}

function expand_extensions_in_program(program_lines, extensions) {
    let expanded = [];
    for (let idx = 0; idx < program_lines.length; idx++) {
        let raw_line = program_lines[idx];
        let line = raw_line.trim();
        if (!line) continue;
        
        let matched_full = false;
        let indent = raw_line.substring(0, raw_line.length - raw_line.trimStart().length);
        
        for (let ext of extensions) {
            let compiled = ext.compiled_pattern;
            let match = compiled.exec(line);
            let is_inline = false;
            
            if (!match) {
                let searchMatch = ext.search_pattern.exec(raw_line);
                if (searchMatch) {
                    match = searchMatch;
                    is_inline = true;
                }
            }
            
            if (match) {
                let env = {};
                if (match.groups) {
                    for (let [k, v] of Object.entries(match.groups)) {
                        let num = Number(v);
                        env[k] = !isNaN(num) && (v.startsWith('0x') || v.startsWith('0X') ? parseInt(v, 16) : num) ? num : v;
                    }
                }
                
                // Note: Logic execution is disabled because this is a browser version (safe_mode = true).
                
                let outputs = [];
                for (let out of ext.output) {
                    let processed_out = out;
                    for (let [k, v] of Object.entries(env)) {
                        processed_out = processed_out.replace(new RegExp(`\\{${k}\\}`, 'g'), String(v));
                    }
                    outputs.push(processed_out);
                }
                
                if (is_inline && outputs.length === 1) {
                    raw_line = raw_line.substring(0, match.index) + outputs[0] + raw_line.substring(match.index + match[0].length);
                    line = raw_line.trim();
                } else {
                    for (let o of outputs) {
                        expanded.push([idx + 1, indent + o]);
                    }
                    matched_full = true;
                    break;
                }
            }
        }
        if (!matched_full) {
            expanded.push([idx + 1, raw_line]);
        }
    }
    return expanded;
}

export { parse_extensions, expand_extensions_in_program };
