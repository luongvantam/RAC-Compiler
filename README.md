# RAC COMPILER

*Read in other languages: [Tiếng Việt](README.vi.md), [中文](README.zh.md).*

---

## ENGLISH GUIDE

### I. INSTALLATION & EXECUTION

#### 1. Download the Compiler

Get the latest source code and distribution releases from the official GitHub repository:

* **Repository Link:** [https://github.com/luongvantam/RAC-Compiler](https://github.com/luongvantam/RAC-Compiler)
* **Method:** Click the **Code** button -> **Download ZIP** and extract it, or execute via Git terminal clone:
```bash
git clone https://github.com/luongvantam/RAC-Compiler.git
```

#### 2. Syntax Highlighting Support

To secure code visual enhancement when coding on Visual Studio Code:

1. Open VS Code and open the Extension tab using `Ctrl + Shift + X` (or `Cmd + Shift + X` on macOS).
2. Click the `...` (Views and More Actions) button at the top right of the Extensions view.
3. Select **Install from VSIX...**
4. Browse and select the `rsc.vsix` file included in this repository to install it.

#### 3. Running & Compiling Code

Depending on your host operating system platform, launch the dedicated automated script file located inside the compiler directory:

* **On Windows Platforms:** Double-click on `run.bat` (or execute via PowerShell/CMD environment).
* **On Linux / macOS Environments:** Launch terminal in the root directory path and execute `run.sh`:
```bash
chmod +x run.sh
./run.sh
```

* **Compilation Process:** 
  1. On first run, it will prompt you to enter the target calculator model (e.g., `580vnx`, `880btg`).
  2. At the main prompt, enter the exact source file name or full path to compile and press `Enter`.
  3. You can use the following interactive commands:
     - `!q`: Quit the compiler.
     - `!m`: Change the target model.
     - `!u`: Check for updates.

#### 4. Using the IDE (New)

The project now includes 2 Integrated Development Environments (IDEs):

* **TUI IDE (Terminal UI):**
  * Run `IDE.bat` on Windows or `./IDE.sh` on Linux/macOS.
  * Features syntax highlighting directly in your terminal.
  * Requires the `textual` Python module (installed automatically via scripts).

* **Web IDE (Browser UI):**
  * Run `web.bat` on Windows or `./web.sh` on Linux/macOS.
  * Open your browser and navigate to the address shown in the terminal (usually `http://localhost:8000`).

---

**Document Maintainer:** `luongvantam`