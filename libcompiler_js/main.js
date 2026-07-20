import * as loader from './loader.js';
import * as engine from './engine.js';
import * as extensions from './extensions.js';
import * as handlers from './handlers.js';
import * as utils from './utils.js';

class RACCompiler {
    constructor() {
        this.files = {};
    }

    setFiles(files) {
        // files: { 'config.json': '...', 'gadgets.txt': '...', 'labels.txt': '...', 'disas.txt': '...', 'extensions.txt': '...', 'keyword.txt': '...' }
        this.files = files;
    }

    compile(program_content, options = {}) {
        utils._default_diagnostics.reset();
        let config_str = this.files['config.json'];
        if (!config_str) {
            return { notifications: [`error: Missing config.json`], output: "" };
        }
        
        let config;
        try {
            config = JSON.parse(config_str);
        } catch (e) {
            return { notifications: [`error: Invalid config.json: ${e.message}`], output: "" };
        }

        Object.assign(loader.char_to_hex, config.char_to_hex || {});
        Object.assign(loader.token_to_hex, config.token_to_hex || {});
        
        if (this.files['keyword.txt']) {
            utils.setKeywords(this.files['keyword.txt'].split('\n').map(l => l.trim()).filter(l => l));
        }
        handlers.init_handlers();

        if (this.files[config.disassembly_file]) {
            loader.parse_disassembly(this.files[config.disassembly_file]);
        }
        
        if (this.files[config.gadgets_file] && this.files[config.labels_file]) {
            try {
                loader.parse_commands(this.files[config.gadgets_file], this.files[config.labels_file]);
            } catch (e) {
                return { notifications: [`error: Failed to parse gadgets/labels: ${e.message}`], output: "" };
            }
        } else {
             return { notifications: [`error: Missing gadgets or labels file`], output: "" };
        }

        let ext_list = [];
        if (this.files[config.extensions_file]) {
            ext_list = extensions.parse_extensions(this.files[config.extensions_file]);
        }

        let raw_content = program_content.split('\n');

    let program;
    try {
        program = extensions.expand_extensions_in_program(raw_content, ext_list);
    } catch (e) {
        return { notifications: [`error: Expanding extensions failed: ${e.message}`], output: "" };
    }

        let overflow_sp = config["overflow_initial_sp"];
        if (overflow_sp === undefined) {
             return { notifications: [`error: Missing overflow_initial_sp in config.json`], output: "" };
        }

        let results;
        try {
            results = engine.process_program(program, overflow_sp);
        } catch (e) {
            if (e instanceof utils.CompilerError) {
                let errs = utils._default_diagnostics.error_buffer.join('\n');
                let notes = utils._default_diagnostics.get_notes();
                let notifs = (errs + '\n' + notes).split('\n').filter(l => l.trim() !== "");
                return { notifications: notifs, output: "" };
            }
            return { notifications: [`error: Internal compiler error: ${e.stack}`], output: "" };
        }
        
        let stdout_str = results.output || "";

        let errs = utils._default_diagnostics.error_buffer.join('\n');
        if (errs) {
            results.notifications = errs.split('\n').filter(l => l.trim() !== "").concat(results.notifications || []);
        }

        return results;
    }
}

export { RACCompiler };
