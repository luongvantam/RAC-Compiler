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

        .token.string .token.parameter { color: #4fc1ff; font-weight: bold; }
        .token.string .token.escape { color: #d7ba7d; }
    `;
    document.head.appendChild(style);


    if (typeof Prism !== "undefined") {

        Prism.languages.rsc = {
            // Hỗ trợ cả comment đơn dòng # và khối comment đa dòng /* ... */
            comment: [
                { pattern: /\/\*[\s\S]*?\*\//, greedy: true },
                { pattern: /#.*/, greedy: true }
            ],

            // Chuỗi nháy kép (hỗ trợ f-string với {parameter}) và chuỗi nháy đơn 'token string'
            string: [
                {
                    pattern: /"(?:\\.|[^"\\])*"/,
                    greedy: true,
                    inside: {
                        parameter: {
                            pattern: /\{[^}]+\}/,
                            alias: "variable"
                        },
                        escape: /~/
                    }
                },
                {
                    pattern: /'(?:\\.|[^'\\])*'/,
                    greedy: true
                }
            ],

            // Định dạng chỉ thị phân vùng: @section.<section> hoặc @set.<section>
            directive: {
                pattern: /^\s*@(set|section)\.[a-zA-Z0-9_]+/m,
                alias: "important"
            },

            // Các modifier khai báo
            "storage-modifier": /\b(lbl|func|def|loop|repeat|find_gadgets)\b/,
            "storage-type": /\b(reg|var|str)\b/,

            // Danh sách các từ khóa chuẩn theo tài liệu Syntax.md
            keyword: /\b(call|goto|eval|org|backup|pr_length|calc|return|hex|py|adr_of|adr_arith)\b/,

            // Biểu thức tính toán khoảng cách backup: dist.<section>
            "distance-helper": {
                pattern: /\bdist\.[a-zA-Z0-9_]+\b/,
                alias: "keyword"
            },

            // Hàm lấy địa chỉ nhãn: adr(...)
            adr: {
                pattern: /\badr(?=\()/,
                alias: "function"
            },

            "python-func": {
                pattern: /(?<=\bpy\.)[a-zA-Z_][a-zA-Z0-9_]*/,
                alias: "function"
            },

            // Định nghĩa hàm: func <tên_hàm> hoặc def <tên_hàm>
            "function-def": {
                pattern: /(?<=\b(func|def)\s)[a-zA-Z_][a-zA-Z0-9_]*/,
                alias: "function"
            },

            // Lời gọi hàm chung: call <tên_hàm> hoặc trực tiếp <tên_hàm>(...)
            "function-call": [
                {
                    pattern: /(?<=\bcall\s)[a-zA-Z_][a-zA-Z0-9_]*/,
                    alias: "function"
                },
                {
                    pattern: /\b[a-zA-Z_][a-zA-Z0-9_]*(?=\()/,
                    alias: "function"
                }
            ],

            // Định nghĩa nhãn: lbl <nhãn> hoặc <nhãn>: ở đầu dòng
            "label-def": [
                {
                    pattern: /(?<=\blbl\s)[a-zA-Z_][a-zA-Z0-9_]*/
                },
                {
                    pattern: /^[ \t]*[a-zA-Z_][a-zA-Z0-9_]*(?=:)/m
                }
            ],

            // Tham chiếu nhãn sau lệnh nhảy: goto <nhãn> hoặc adr_of <nhãn>
            "label-ref": [
                {
                    pattern: /(?<=\bgoto\s)[a-zA-Z_][a-zA-Z0-9_]*/
                },
                {
                    pattern: /(?<=\badr_of\s(?:\[[^\]]*\]\s*)?)[a-zA-Z_][a-zA-Z0-9_]*/
                }
            ],

            // Tập thanh ghi tiêu chuẩn
            register: {
                pattern: /\b([erxqr]{1,2}[0-9]{1,2}|sp|pc|ea)\b/i,
                alias: "variable"
            },

            constant: /\bKEY_[A-Z0-9_]+\b/,

            // Hệ cơ số 16 (0x...) và số nguyên thường
            number: [
                /\b0x[0-9a-fA-F]+\b/,
                /\b\d+\b/
            ],

            operator: /==|!=|=|\+|-|\*|\/|%/,

            punctuation: /[()\[\]{},;:]/
        };

    }

})();