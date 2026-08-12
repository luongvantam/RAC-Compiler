const vscode = require('vscode');
const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');

let statusBarItem;
let pythonCommand = 'python3';

exec('python3 --version', (err) => {
    if (err) {
        pythonCommand = 'python';
    }
});

function getModel(context) {
    return context.workspaceState.get('rscModel');
}

function getMode(context) {
    return context.workspaceState.get('rscMode', 'No Safe Mode');
}

function updateStatusBar(context) {
    const model = getModel(context) || '580vnx (Default)';
    const mode = getMode(context);
    statusBarItem.text = `$(gear) RSC: ${model} | ${mode}`;
    statusBarItem.show();
}

async function ensureCompilerPath(context) {
    let compilerPath = vscode.workspace.getConfiguration('racCompiler').get('path');
    
    if (!compilerPath || !fs.existsSync(path.join(compilerPath, 'rac.py'))) {
        if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
            for (const folder of vscode.workspace.workspaceFolders) {
                if (fs.existsSync(path.join(folder.uri.fsPath, 'rac.py'))) {
                    compilerPath = folder.uri.fsPath;
                    await vscode.workspace.getConfiguration('racCompiler').update('path', compilerPath, vscode.ConfigurationTarget.Global);
                    break;
                }
            }
        }
    }

    if (!compilerPath || !fs.existsSync(path.join(compilerPath, 'rac.py'))) {
        const selected = await vscode.window.showOpenDialog({
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select RAC-Compiler Folder (contains rac.py)',
            title: 'Select RAC-Compiler Directory'
        });
        
        if (selected && selected[0]) {
            compilerPath = selected[0].fsPath;
            if (!fs.existsSync(path.join(compilerPath, 'rac.py'))) {
                vscode.window.showErrorMessage("The selected directory does not contain rac.py!");
                return undefined;
            }
            await vscode.workspace.getConfiguration('racCompiler').update('path', compilerPath, vscode.ConfigurationTarget.Global);
        } else {
            return undefined;
        }
    }
    return compilerPath;
}

async function ensureModel(context) {
    let model = getModel(context);
    if (!model) {
        model = await vscode.commands.executeCommand('rsc.selectModel');
        if (!model) {
            return undefined;
        }
    }
    return model;
}


let diagnosticCollection;
let diagnosticTimeout = null;
const cachedModelSymbols = new Map();

const KEYWORDS = [
    'org', 'backup', 'var', 'reg', 'fill', 'align', 'pad', 'pad_abs', 
    'eval', 'calc', 'goto', 'call', 'lbl', 'def', 'repeat', 'loop', 'func', 
    'pr_length', 'pr_org', 'pr_backup', 'dist', 'sizeof', 'adr', 'hex', 'str'
];

const keywordItems = KEYWORDS.map(kw => {
    const item = new vscode.CompletionItem(kw, vscode.CompletionItemKind.Keyword);
    item.detail = 'RAC Compiler Keyword';
    return item;
});

const sectionItems = [
    new vscode.CompletionItem('@section.', vscode.CompletionItemKind.Module),
    new vscode.CompletionItem('@set.', vscode.CompletionItemKind.Module),
    new vscode.CompletionItem('@build', vscode.CompletionItemKind.Struct)
];

function getModelSymbols(compilerPath, model) {
    const key = `${compilerPath}:${model}`;
    if (cachedModelSymbols.has(key)) return cachedModelSymbols.get(key);

    const items = [];
    if (!compilerPath || !model) return items;

    const modelDir = path.join(compilerPath, model);
    
    // Load gadgets.txt
    const gadgetsPath = path.join(modelDir, 'gadgets.txt');
    if (fs.existsSync(gadgetsPath)) {
        try {
            const content = fs.readFileSync(gadgetsPath, 'utf8');
            for (const line of content.split('\n')) {
                const trimmed = line.trim();
                if (!trimmed || trimmed.startsWith('#')) continue;
                const parts = trimmed.split(/\s+/);
                if (parts.length >= 2) {
                    const addr = parts[0];
                    const name = parts.slice(1).join(' ');
                    const item = new vscode.CompletionItem(name, vscode.CompletionItemKind.Function);
                    item.detail = `Gadget (0x${addr})`;
                    item.documentation = new vscode.MarkdownString(`Gadget \`${name}\` defined at address \`0x${addr}\` for model \`${model}\`.`);
                    items.push(item);
                }
            }
        } catch (e) {}
    }

    // Load labels.txt
    const labelsPath = path.join(modelDir, 'labels.txt');
    if (fs.existsSync(labelsPath)) {
        try {
            const content = fs.readFileSync(labelsPath, 'utf8');
            for (const line of content.split('\n')) {
                const trimmed = line.trim();
                if (!trimmed || trimmed.startsWith('#')) continue;
                const parts = trimmed.split(/\s+/);
                if (parts.length >= 2) {
                    const addr = parts[0];
                    const namesStr = parts.slice(1).join(' ');
                    const names = namesStr.split(';').map(n => n.trim()).filter(Boolean);
                    for (const name of names) {
                        const item = new vscode.CompletionItem(name, vscode.CompletionItemKind.Reference);
                        item.detail = `Model Label (0x${addr})`;
                        item.documentation = new vscode.MarkdownString(`Label \`${name}\` at address \`0x${addr}\` for model \`${model}\`.`);
                        items.push(item);
                    }
                }
            }
        } catch (e) {}
    }

    cachedModelSymbols.set(key, items);
    return items;
}

function getLocalDocumentSymbols(document) {
    const items = [];
    const text = document.getText();
    const lines = text.split('\n');
    const seen = new Set();
    const reservedWords = new Set(['var', 'reg', 'def', 'func', 'lbl', 'org', 'backup', 'repeat', 'loop', 'goto', 'call', 'hex', 'str', 'eval', 'calc']);

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line || line.startsWith('#') || line.startsWith('/*')) continue;

        let match = /^lbl\s+([a-zA-Z0-9_]+)/.exec(line) || /^([a-zA-Z0-9_]+)\s*:/.exec(line);
        if (match) {
            const name = match[1];
            if (!seen.has(name) && !reservedWords.has(name)) {
                seen.add(name);
                const item = new vscode.CompletionItem(name, vscode.CompletionItemKind.Label);
                item.detail = `Local Label (line ${i + 1})`;
                items.push(item);
            }
            continue;
        }

        match = /^(?:func|def)\s+(?:\{[^}]+\}\s+)?([a-zA-Z0-9_]+)/.exec(line);
        if (match) {
            const name = match[1];
            if (!seen.has(name) && !reservedWords.has(name)) {
                seen.add(name);
                const item = new vscode.CompletionItem(name, vscode.CompletionItemKind.Function);
                item.detail = `Function/Macro Def (line ${i + 1})`;
                items.push(item);
            }
            continue;
        }

        match = /^(?:var|reg)\s+([a-zA-Z0-9_]+)/.exec(line) || /^([a-zA-Z0-9_]+)\s*=/.exec(line);
        if (match) {
            const name = match[1];
            if (!seen.has(name) && !reservedWords.has(name)) {
                seen.add(name);
                const item = new vscode.CompletionItem(name, vscode.CompletionItemKind.Variable);
                item.detail = `Variable (line ${i + 1})`;
                items.push(item);
            }
            continue;
        }

        match = /as\s+([a-zA-Z0-9_]+)$/.exec(line);
        if (match) {
            const name = match[1];
            if (!seen.has(name) && !reservedWords.has(name)) {
                seen.add(name);
                const item = new vscode.CompletionItem(name, vscode.CompletionItemKind.Variable);
                item.detail = `Alias (line ${i + 1})`;
                items.push(item);
            }
            continue;
        }
    }
    return items;
}

function triggerDiagnostics(document, context) {
    if (!document || document.languageId !== 'rsc') return;
    if (diagnosticTimeout) clearTimeout(diagnosticTimeout);

    diagnosticTimeout = setTimeout(() => {
        runDiagnostics(document, context);
    }, 400);
}

async function runDiagnostics(document, context) {
    if (!document || document.languageId !== 'rsc') return;

    let compilerPath = vscode.workspace.getConfiguration('racCompiler').get('path');
    if (!compilerPath || !fs.existsSync(path.join(compilerPath, 'rac.py'))) {
        if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
            for (const folder of vscode.workspace.workspaceFolders) {
                if (fs.existsSync(path.join(folder.uri.fsPath, 'rac.py'))) {
                    compilerPath = folder.uri.fsPath;
                    break;
                }
            }
        }
    }

    if (!compilerPath || !fs.existsSync(path.join(compilerPath, 'rac.py'))) {
        return;
    }

    const model = getModel(context) || '580vnx';
    const filePath = document.uri.fsPath;

    const command = `"${pythonCommand}" "${path.join(compilerPath, 'rac.py')}" "${model}" "${filePath}"`;
    exec(command, { cwd: compilerPath }, (error, stdout, stderr) => {
        const diagnostics = [];
        const output = (stderr || '') + '\n' + (stdout || '');

        const errorRegex = /error:\s*([^\n]+)\n\s*-->\s*([^\n]+):(\d+)\n\s*\|\n\d+\s*\|\s*([^\n]+)\n\s*\|\s*(\s*)(\^+)/g;
        let match;
        while ((match = errorRegex.exec(output)) !== null) {
            const message = match[1].trim();
            const line = parseInt(match[3], 10) - 1;
            const paddingStr = match[5];
            const caretCount = match[6].length;
            const startCol = paddingStr.length;
            const endCol = startCol + caretCount;

            const range = new vscode.Range(
                new vscode.Position(line, startCol),
                new vscode.Position(line, endCol)
            );
            const diag = new vscode.Diagnostic(range, message, vscode.DiagnosticSeverity.Error);
            diagnostics.push(diag);
        }

        if (diagnostics.length === 0 && error && output.includes('error:')) {
            const generalMatch = /error:\s*([^\n]+)/.exec(output);
            const msg = generalMatch ? generalMatch[1].trim() : "Compilation error";
            const range = new vscode.Range(0, 0, 0, 100);
            diagnostics.push(new vscode.Diagnostic(range, msg, vscode.DiagnosticSeverity.Error));
        }

        diagnosticCollection.set(document.uri, diagnostics);
    });
}


function activate(context) {
    console.log("RSC Extension is activating!");
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.command = 'rsc.selectModel';

    context.subscriptions.push(statusBarItem);
    updateStatusBar(context);

    diagnosticCollection = vscode.languages.createDiagnosticCollection('rsc');
    context.subscriptions.push(diagnosticCollection);

    // Register Auto-Completion Provider
    context.subscriptions.push(
        vscode.languages.registerCompletionItemProvider('rsc', {
            provideCompletionItems(document, position, token, contextProvider) {
                const compilerPath = vscode.workspace.getConfiguration('racCompiler').get('path');
                const model = getModel(context) || '580vnx';

                const modelItems = getModelSymbols(compilerPath, model);
                const localItems = getLocalDocumentSymbols(document);

                return [...keywordItems, ...sectionItems, ...modelItems, ...localItems];
            }
        }, '@', '.')
    );

    // Real-time diagnostics listeners
    if (vscode.window.activeTextEditor) {
        triggerDiagnostics(vscode.window.activeTextEditor.document, context);
    }

    context.subscriptions.push(
        vscode.window.onDidChangeActiveTextEditor(editor => {
            if (editor) triggerDiagnostics(editor.document, context);
        }),
        vscode.workspace.onDidChangeTextDocument(e => {
            triggerDiagnostics(e.document, context);
        }),
        vscode.workspace.onDidSaveTextDocument(doc => {
            triggerDiagnostics(doc, context);
        })
    );

    context.subscriptions.push(vscode.commands.registerCommand('rsc.selectModel', async () => {
        const currentModel = getModel(context) || '580vnx';
        const selected = await vscode.window.showInputBox({
            prompt: 'Enter RAC Compiler Model (e.g. 580vnx, 880btg, etc.)',
            value: currentModel,
            placeHolder: 'Model name'
        });
        if (selected && selected.trim() !== '') {
            await context.workspaceState.update('rscModel', selected.trim());
            updateStatusBar(context);
            return selected.trim();
        }
        return getModel(context);
    }));

    context.subscriptions.push(vscode.commands.registerCommand('rsc.selectMode', async () => {
        const selected = await vscode.window.showQuickPick(['No Safe Mode', 'Safe Mode'], {
            placeHolder: 'Select RAC Compiler Execution Mode'
        });
        if (selected) {
            await context.workspaceState.update('rscMode', selected);
            updateStatusBar(context);
        }
    }));

    context.subscriptions.push(vscode.commands.registerCommand('rsc.setCompilerPath', async () => {
        const selected = await vscode.window.showOpenDialog({
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select RAC-Compiler Folder',
            title: 'Select RAC-Compiler Directory'
        });
        if (selected && selected[0]) {
            const compilerPath = selected[0].fsPath;
            if (!fs.existsSync(path.join(compilerPath, 'rac.py'))) {
                vscode.window.showErrorMessage("The selected directory does not contain rac.py!");
                return;
            }
            await vscode.workspace.getConfiguration('racCompiler').update('path', compilerPath, vscode.ConfigurationTarget.Global);
            vscode.window.showInformationMessage(`RAC Compiler path set to: ${compilerPath}`);
        }
    }));

    context.subscriptions.push(vscode.commands.registerCommand('rsc.run', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) return;

        const document = editor.document;
        if (document.languageId !== 'rsc') return;

        if (document.isDirty) {
            await document.save();
        }

        const model = await ensureModel(context);
        if (!model) return;
        
        const compilerPath = await ensureCompilerPath(context);
        if (!compilerPath) return;
        
        const mode = getMode(context);
        const racPy = path.join(compilerPath, 'rac.py');

        let flags = '';
        if (mode === 'Safe Mode') {
            flags = '--safe';
        }

        let terminal = vscode.window.terminals.find(t => t.name === 'RAC Compiler');
        if (!terminal) {
            terminal = vscode.window.createTerminal({ name: 'RAC Compiler', cwd: compilerPath });
        }
        
        terminal.show();
        terminal.sendText('clear'); 
        terminal.sendText(`${pythonCommand} "${racPy}" "${model}" "${document.uri.fsPath}" ${flags}`);
    }));

    context.subscriptions.push(vscode.commands.registerCommand('rsc.debug', async () => {
        vscode.commands.executeCommand('workbench.action.debug.start');
    }));

    context.subscriptions.push(vscode.debug.registerDebugConfigurationProvider('rsc', {
        resolveDebugConfiguration(folder, config, token) {
            if (!config.type && !config.request && !config.name) {
                const editor = vscode.window.activeTextEditor;
                if (editor && editor.document.languageId === 'rsc') {
                    config.type = 'rsc';
                    config.name = 'Launch RSC';
                    config.request = 'launch';
                    config.program = '${file}';
                }
            }

            if (!config.program) {
                return vscode.window.showInformationMessage("Cannot find a program to debug").then(_ => {
                    return undefined; 
                });
            }

            return config;
        }
    }));

    context.subscriptions.push(vscode.debug.registerDebugAdapterDescriptorFactory('rsc', {
        createDebugAdapterDescriptor(session, executable) {
            return new vscode.DebugAdapterInlineImplementation(new RscDebugAdapter(context));
        }
    }));
}

class RscDebugAdapter {
    constructor(context) {
        this.context = context;
        this._sendMessage = new vscode.EventEmitter();
        this.onDidSendMessage = this._sendMessage.event;
        this._seq = 1;
        this._errorInfo = null;
    }

    sendEvent(event, body) {
        this._sendMessage.fire({
            seq: this._seq++,
            type: 'event',
            event: event,
            body: body
        });
    }

    sendResponse(request, body) {
        this._sendMessage.fire({
            seq: this._seq++,
            type: 'response',
            request_seq: request.seq,
            command: request.command,
            success: true,
            body: body
        });
    }

    handleMessage(message) {
        if (message.type === 'request') {
            switch (message.command) {
                case 'initialize':
                    this.sendResponse(message, {
                        supportsConfigurationDoneRequest: true,
                        supportsExceptionInfoRequest: true
                    });
                    this.sendEvent('initialized');
                    break;
                case 'launch':
                    this.sendResponse(message);
                    if (message.arguments.noDebug) {
                        this.runInTerminal(message.arguments.program);
                    } else {
                        this.compileAndCheck(message.arguments.program);
                    }
                    break;
                case 'configurationDone':
                    this.sendResponse(message);
                    break;
                case 'threads':
                    this.sendResponse(message, {
                        threads: [{ id: 1, name: "Main Thread" }]
                    });
                    break;
                case 'stackTrace':
                    if (this._errorInfo) {
                        this.sendResponse(message, {
                            stackFrames: [{
                                id: 1,
                                name: "Compiler Output",
                                source: { 
                                    name: path.basename(this._errorInfo.file), 
                                    path: this._errorInfo.file 
                                },
                                line: this._errorInfo.line,
                                column: this._errorInfo.column
                            }]
                        });
                    } else {
                        this.sendResponse(message, { stackFrames: [] });
                    }
                    break;
                case 'exceptionInfo':
                    if (this._errorInfo) {
                        this.sendResponse(message, {
                            exceptionId: "CompilerError",
                            description: this._errorInfo.message,
                            breakMode: "always",
                            details: {
                                message: this._errorInfo.message,
                                typeName: "CompilerError"
                            }
                        });
                    } else {
                        this.sendResponse(message);
                    }
                    break;
                case 'disconnect':
                    this.sendResponse(message);
                    break;
                default:
                    this.sendResponse(message);
                    break;
            }
        }
    }

    async runInTerminal(programPath) {
        if (!programPath) {
            const editor = vscode.window.activeTextEditor;
            programPath = editor ? editor.document.uri.fsPath : null;
        }
        if (!programPath) {
            vscode.window.showErrorMessage("No file selected for running.");
            this.sendEvent('exited', { exitCode: 1 });
            this.sendEvent('terminated');
            return;
        }

        const model = await ensureModel(this.context);
        if (!model) {
            this.sendEvent('exited', { exitCode: 1 });
            this.sendEvent('terminated');
            return;
        }
        
        const compilerPath = await ensureCompilerPath(this.context);
        if (!compilerPath) {
            this.sendEvent('exited', { exitCode: 1 });
            this.sendEvent('terminated');
            return;
        }
        
        const mode = getMode(this.context);
        const racPy = path.join(compilerPath, 'rac.py');
        
        let flags = mode === 'Safe Mode' ? '--safe' : '';
        
        let terminal = vscode.window.terminals.find(t => t.name === 'RAC Compiler');
        if (!terminal) {
            terminal = vscode.window.createTerminal({ name: 'RAC Compiler', cwd: compilerPath });
        }
        
        terminal.show();
        terminal.sendText('clear');
        terminal.sendText(`${pythonCommand} "${racPy}" "${model}" "${programPath}" ${flags}`);

        this.sendEvent('exited', { exitCode: 0 });
        this.sendEvent('terminated');
    }

    async compileAndCheck(programPath) {
        if (!programPath) {
            const editor = vscode.window.activeTextEditor;
            if (editor) {
                programPath = editor.document.uri.fsPath;
            } else {
                vscode.window.showErrorMessage("No file selected for debugging.");
                this.sendEvent('exited', { exitCode: 1 });
                this.sendEvent('terminated');
                return;
            }
        }
        
        const model = await ensureModel(this.context);
        if (!model) {
            this.sendEvent('exited', { exitCode: 1 });
            this.sendEvent('terminated');
            return;
        }

        const compilerPath = await ensureCompilerPath(this.context);
        if (!compilerPath) {
            this.sendEvent('exited', { exitCode: 1 });
            this.sendEvent('terminated');
            return;
        }

        const mode = getMode(this.context);
        const racPy = path.join(compilerPath, 'rac.py');
        
        let flags = mode === 'Safe Mode' ? '--safe' : '';
        const args = `"${racPy}" "${model}" "${programPath}" ${flags}`;
        
        let terminal = vscode.window.terminals.find(t => t.name === 'RAC Compiler');
        if (!terminal) {
            terminal = vscode.window.createTerminal({ name: 'RAC Compiler', cwd: compilerPath });
        }
        setTimeout(() => terminal.show(false), 500);
        terminal.sendText('clear');
        terminal.sendText(`${pythonCommand} "${racPy}" "${model}" "${programPath}" ${flags}`);

        exec(`"${pythonCommand}" ${args}`, { cwd: compilerPath }, (error, stdout, stderr) => {
            if (error && stderr) {
                const errorRegex = /error:\s*([^\n]+)\n\s*-->\s*([^\n]+):(\d+)\n\s*\|\n\d+\s*\|\s*([^\n]+)\n\s*\|\s*(\s*)(\^+)/;
                const match = errorRegex.exec(stderr);
                
                if (match) {
                    const message = match[1].trim();
                    const line = parseInt(match[3], 10);
                    const paddingStr = match[5];
                    const startCol = paddingStr.length + 1;
                    
                    this._errorInfo = {
                        message: message,
                        file: programPath,
                        line: line,
                        column: startCol
                    };
                } else {
                    const matchGeneral = /error:\s*([^\n]+)/.exec(stderr);
                    const msg = matchGeneral ? matchGeneral[1].trim() : stderr.trim().split('\n')[0];
                    this._errorInfo = {
                        message: msg,
                        file: programPath,
                        line: 1,
                        column: 1
                    };
                }
                
                this.sendEvent('stopped', {
                    reason: 'exception',
                    threadId: 1,
                    text: this._errorInfo.message,
                    description: 'Exception has occurred',
                    allThreadsStopped: true
                });
                return;
            }
            
            this.sendEvent('exited', { exitCode: error ? error.code : 0 });
            this.sendEvent('terminated');
        });
    }

    dispose() {}
}

function deactivate() {
    if (statusBarItem) {
        statusBarItem.dispose();
    }
}

module.exports = {
    activate,
    deactivate
};
