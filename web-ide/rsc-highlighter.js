(function () {

    const style = document.createElement("style");
    style.innerHTML = `
        .token.comment { color: #6a9955; font-style: italic; }
        .token.string { color: #ce9178; }
        .token.keyword { color: #569cd6; font-weight: bold; }
        .token.storage-type { color: #4ec9b0; }
        .token.storage-modifier { color: #c586c0; }
        .token.register { color: #9cdcfe; }
        .token.number { color: #b5cea8; }
        .token.operator { color: #d4d4d4; }
        .token.punctuation { color: #808080; }
        .token.directive { color: #c586c0; font-weight: bold; }
        .token.function-def { color: #dcdcaa; font-weight: bold; }
        .token.function-call { color: #dcdcaa; }
        .token.label-def { color: #4fc1ff; text-decoration: underline; font-weight: bold; }
        .token.label-ref { color: #4fc1ff; }
        .token.python-func { color: #dcdcaa; }
        .token.support-variable { color: #9cdcfe; font-style: italic; }

        .token.string .token.parameter { color: #4fc1ff; font-weight: bold; }
        .token.string .token.escape { color: #d7ba7d; }
    `;
    document.head.appendChild(style);


    window.initRscHighlighter = function(syntaxData) {
        if (typeof Prism === "undefined") return;

        let rsc = {
            // Static rules (not in syntax.json since they use specific Prism features like inside/greedy)
            comment: [
                { pattern: /\/\*[\s\S]*?\*\//, greedy: true },
                { pattern: /#.*/, greedy: true }
            ],
            string: [
                {
                    pattern: /"(?:\\.|[^"\\])*"/,
                    greedy: true,
                    inside: {
                        parameter: { pattern: /\{[^}]+\}/, alias: "variable" },
                        escape: /~/
                    }
                },
                { pattern: /'(?:\\.|[^'\\])*'/, greedy: true }
            ]
        };

        const ALIAS_MAP = {
            "directive": "important",
            "support_variable": "variable",
            "distance_helper": "keyword",
            "builtin": "function",
            "python_func": "function",
            "function_def": "function",
            "function_call": "function",
            "function_call_direct": "function",
            "register": "variable",
            "number_hex_array": "number",
            "number_hex": "number",
            "number_hex_byte": "number",
            "number_dec": "number"
        };

        let tempRules = {};

        for (let rule of syntaxData.rules) {
            let id = rule.id;
            let regexStr = rule.regex;
            let flags = rule.flags_js || "";
            let obj = { pattern: new RegExp(regexStr, flags) };
            if (rule.group === 2) obj.lookbehind = true;
            if (ALIAS_MAP[id]) obj.alias = ALIAS_MAP[id];
            
            tempRules[id] = obj;
        }

        // Map parsed rules to Prism token names
        rsc["directive"] = tempRules["directive"];
        rsc["support-variable"] = tempRules["support_variable"];
        rsc["storage-modifier"] = tempRules["storage_modifier"];
        rsc["storage-type"] = tempRules["storage_type"];
        rsc["keyword"] = tempRules["keyword"];
        rsc["distance-helper"] = tempRules["distance_helper"];
        rsc["builtin"] = tempRules["builtin"];
        rsc["python-func"] = tempRules["python_func"];
        rsc["function-def"] = tempRules["function_def"];
        rsc["function-call"] = [tempRules["function_call"], tempRules["function_call_direct"]];
        rsc["label-def"] = [tempRules["label_def_1"], tempRules["label_def_2"]];
        rsc["label-ref"] = [tempRules["label_ref_1"], tempRules["label_ref_2"]];
        rsc["register"] = tempRules["register"];
        rsc["constant"] = tempRules["constant"];
        rsc["number"] = [tempRules["number_hex"], tempRules["number_hex_array"], tempRules["number_hex_byte"], tempRules["number_dec"]];
        rsc["operator"] = tempRules["operator"];
        rsc["punctuation"] = tempRules["punctuation"];

        Prism.languages.rsc = rsc;
    };

})();