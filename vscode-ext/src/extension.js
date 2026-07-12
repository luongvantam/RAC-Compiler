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

async function ensureModel(context) {
    let model = getModel(context);
    if (!model) {
        model = await vscode.commands.executeCommand('rsc.selectModel');
    }
    return model || '580vnx';
}

function activate(context) {
    console.log("RSC Extension is activating!");
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.command = 'rsc.selectModel';

    context.subscriptions.push(statusBarItem);

    updateStatusBar(context);

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

    context.subscriptions.push(vscode.commands.registerCommand('rsc.run', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) return;

        const document = editor.document;
        if (document.languageId !== 'rsc') return;

        if (document.isDirty) {
            await document.save();
        }

        const model = await ensureModel(context);
        const mode = getMode(context);
        
        const workspaceFolder = vscode.workspace.getWorkspaceFolder(document.uri);
        const cwd = workspaceFolder ? workspaceFolder.uri.fsPath : path.dirname(document.uri.fsPath);
        
        const racPy = path.join(cwd, 'rac.py');
        if (!fs.existsSync(racPy)) {
            vscode.window.showErrorMessage("rac.py not found in workspace root!");
            return;
        }

        let flags = '';
        if (mode === 'Safe Mode') {
            flags = '--safe';
        }

        let terminal = vscode.window.terminals.find(t => t.name === 'RAC Compiler');
        if (!terminal) {
            terminal = vscode.window.createTerminal({ name: 'RAC Compiler', cwd: cwd });
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
        const mode = getMode(this.context);
        
        const workspaceFolder = vscode.workspace.getWorkspaceFolder(vscode.Uri.file(programPath));
        const cwd = workspaceFolder ? workspaceFolder.uri.fsPath : path.dirname(programPath);
        const racPy = path.join(cwd, 'rac.py');
        
        let flags = mode === 'Safe Mode' ? '--safe' : '';
        
        let terminal = vscode.window.terminals.find(t => t.name === 'RAC Compiler');
        if (!terminal) {
            terminal = vscode.window.createTerminal({ name: 'RAC Compiler', cwd: cwd });
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
        const mode = getMode(this.context);
        
        const workspaceFolder = vscode.workspace.getWorkspaceFolder(vscode.Uri.file(programPath));
        const cwd = workspaceFolder ? workspaceFolder.uri.fsPath : path.dirname(programPath);
        const racPy = path.join(cwd, 'rac.py');
        
        let flags = mode === 'Safe Mode' ? '--safe' : '';
        const args = `"${racPy}" "${model}" "${programPath}" ${flags}`;
        
        let terminal = vscode.window.terminals.find(t => t.name === 'RAC Compiler');
        if (!terminal) {
            terminal = vscode.window.createTerminal({ name: 'RAC Compiler', cwd: cwd });
        }
        setTimeout(() => terminal.show(false), 500);
        terminal.sendText('clear');
        terminal.sendText(`${pythonCommand} "${racPy}" "${model}" "${programPath}" ${flags}`);

        exec(`"${pythonCommand}" ${args}`, { cwd }, (error, stdout, stderr) => {
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
