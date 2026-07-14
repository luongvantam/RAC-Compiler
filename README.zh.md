# RAC COMPILER

*阅读其他语言版本: [English](README.md), [Tiếng Việt](README.vi.md).*

---

## 中文指南

### I. 安装与运行

#### 1. 下载编译器

从官方 GitHub 仓库获取最新的源代码和发布版本：

* **仓库链接:** [https://github.com/luongvantam/RAC-Compiler](https://github.com/luongvantam/RAC-Compiler)
* **方法:** 点击 **Code** 按钮 -> **Download ZIP** 并解压，或者通过 Git 终端克隆：
```bash
git clone https://github.com/luongvantam/RAC-Compiler.git
```

#### 2. 语法高亮支持

为了在 Visual Studio Code 编写代码时获得更好的视觉体验：

1. 打开 VS Code，使用 `Ctrl + Shift + X`（在 macOS 上使用 `Cmd + Shift + X`）打开扩展选项卡。
2. 点击扩展视图右上角的 `...`（视图和更多操作）按钮。
3. 选择 **Install from VSIX...**（从 VSIX 安装...）
4. 浏览并选择此仓库中包含的 `rsc.vsix` 文件进行安装。

#### 3. 运行和编译代码

根据您的主机操作系统平台，启动位于编译器目录下的专用自动脚本文件：

* **在 Windows 平台上:** 双击 `run.bat`（或通过 PowerShell/CMD 环境执行）。
* **在 Linux / macOS 环境下:** 在根目录路径下启动终端并执行 `run.sh`：
```bash
chmod +x run.sh
./run.sh
```

* **编译过程:** 
  1. 首次运行时，会提示您输入目标计算器型号（例如 `580vnx`，`880btg`）。
  2. 在主提示符下，输入要编译的确切源文件名或完整路径，然后按 `Enter`。
  3. 您可以使用以下交互式命令：
     - `!q`: 退出编译器。
     - `!m`: 更改目标型号。
     - `!u`: 检查更新。

#### 4. 使用 IDE (新增)

该项目现在包含 2 个集成开发环境 (IDE)：

* **TUI IDE (终端用户界面):**
  * 在 Windows 上运行 `IDE.bat` 或在 Linux/macOS 上运行 `./IDE.sh`。
  * 直接在您的终端中提供语法高亮功能。
  * 需要 `textual` Python 模块（通过脚本自动安装）。

* **Web IDE (浏览器用户界面):**
  * 在 Windows 上运行 `web.bat` 或在 Linux/macOS 上运行 `./web.sh`。
  * 打开浏览器并导航到终端中显示的地址（通常是 `http://localhost:8000`）。

---

**文档维护者:** `luongvantam`
