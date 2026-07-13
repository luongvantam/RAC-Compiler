import os
import sys
import subprocess
import re
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from textual import work
from check_update import check_update_available, perform_update, get_config, save_config
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, TextArea, RichLog, TabbedContent, TabPane, Button, Tree, Label, Input, ListView, ListItem
from textual.scroll_view import ScrollView
from textual.geometry import Size
from textual.strip import Strip
from textual.binding import Binding
from textual.screen import ModalScreen
from textual import events, on
from textual.command import Provider, Hit
from rich.style import Style
from rich.segment import Segment
from rsc_highlighter import (
    S_KEY, S_PUNCT, S_OPERATOR, S_SUPPORT, S_DIRECTIVE, S_LABEL_REF, S_LABEL,
    S_BUILTIN, S_FUNCTION, S_REGISTER, S_HEX_BYTE, S_NUMBER, S_STORAGE,
    S_KEYWORD_OP, S_KEYWORD, S_STRING, S_COMMENT
)
try:
    from rsc_highlighter import make_segments, S_DEFAULT
    HAS_RSC_HIGHLIGHT = True
except ImportError:
    HAS_RSC_HIGHLIGHT = False
    S_DEFAULT = None


from widgets import SearchResultItem, MobileTabsContainer, VerticalResizer, DiskVirtualViewer
from editor import CtxTextArea, RscTextArea
from modals import UpdateModal, ModelSelectModal, ContextMenu
from commands import IDECommandProvider

class RSC_IDE(App):
    COMMANDS = App.COMMANDS | {IDECommandProvider}
    
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        Binding("ctrl+s", "save_files", "Save", show=True),
        Binding("ctrl+r", "compile_run", "Run", show=True),
        Binding("ctrl+f", "toggle_search", "Find", show=True),
        Binding("ctrl+o", "goto_workspace", "Workspace", show=True),
        Binding("ctrl+z", "editor_undo", "Undo", show=False),
        Binding("ctrl+y", "editor_redo", "Redo", show=False),
        Binding("ctrl+c", "editor_copy", "Copy", show=False),
        Binding("ctrl+v", "editor_paste", "Paste", show=False),
        Binding("ctrl+x", "editor_cut", "Cut", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.current_filepath = None
        self.model_name = None
        self.update_status = "Checking..."
        self.model_files = ["labels.txt", "gadgets.txt", "extensions.txt", "disas.txt"]
        self.is_mobile = False
        self.long_press_timer = None

    def compose(self) -> ComposeResult:
        yield Header()
        
        
        with MobileTabsContainer(id="mobile-tabs"):
            yield Button("Cmd", id="mtab-cmd", classes="mtab-btn")
            yield Button("Workspace", id="mtab-workspace", classes="mtab-btn")
            yield Button("Editor", id="mtab-editor", classes="mtab-btn")
            yield Button("Models", id="mtab-models", classes="mtab-btn")
            yield Button("Find", id="mtab-find", classes="mtab-btn")
            yield Button("Output", id="mtab-output", classes="mtab-btn")
            
        with Horizontal(id="main-container"):
            with Vertical(id="activity-bar"):
                yield Button("Cmd", id="act-cmd", classes="activity-btn")
                yield Button("WS", id="act-workspace", classes="activity-btn -active")
                yield Button("Find", id="act-find", classes="activity-btn")
                yield Button("Run", id="act-run", classes="activity-btn")
            
            with Vertical(id="workspace-pane"):
                with Horizontal(id="ws-header"):
                    yield Label("Workspace", id="ws-title", classes="text-bold")
                yield Tree("Workspace", id="workspace-tree")

            with Vertical(id="sidebar"):
                with Horizontal(id="search-header"):
                    yield Label("Code Search", classes="text-bold")
                
                with Horizontal(id="search-row"):
                    yield Input(placeholder="Search", id="global-search-input")
                    with Horizontal(id="search-toggles"):
                        yield Button("Aa", id="btn-case", classes="mini-toggle")
                        yield Button(".*", id="btn-regex", classes="mini-toggle")
                
                with Horizontal(id="replace-row"):
                    yield Input(placeholder="Replace", id="global-replace-input")
                    with Horizontal(id="replace-toggles"):
                        yield Button("Rep", id="btn-replace", classes="mini-toggle")
                        yield Button("All", id="btn-replace-all", classes="mini-toggle")
                
                with Vertical(id="search-results-container"):
                    yield ListView(id="search-results")
                
            yield VerticalResizer(["workspace-pane", "sidebar"], id="left-resizer", classes="resizer")
            
            with Vertical(id="editor-container"):
                with Horizontal(id="editor-toolbar"):
                    yield Button("Run", id="tb-run", classes="tb-btn", variant="success")
                    yield Button("Save", id="tb-save", classes="tb-btn", variant="primary")
                    yield Button("Undo", id="tb-undo", classes="tb-btn")
                    yield Button("Redo", id="tb-redo", classes="tb-btn")
                editor = RscTextArea(id="editor-area", language=None, soft_wrap=True, show_line_numbers=True) 
                editor.border_title = "Editor"
                yield editor
            
            yield VerticalResizer(["right-pane"], is_right=True, id="right-resizer", classes="resizer")
            
            with Vertical(id="right-pane"):
                with TabbedContent(id="model-tabs"):
                    for fname in self.model_files:
                        safe_fname = fname.replace('.', '-')
                        with TabPane(fname, id=f"tab-{safe_fname}"):
                            path = os.path.join(self.project_root, self.model_name or "", fname)
                            if fname == "disas.txt":
                                yield DiskVirtualViewer(filepath=path, id=f"model-editor-{safe_fname}")
                            else:
                                ta = CtxTextArea(id=f"model-editor-{safe_fname}", language="python", show_line_numbers=True)
                                yield ta
                            
                log = CtxTextArea(id="output-log", read_only=True)
                log.border_title = "Output Console"
                yield log

        yield Footer()

    def reload_model_files(self):
        self.sub_title = f"Model: {self.model_name}" if self.model_name else ""
        for fname in self.model_files:
            safe_fname = fname.replace('.', '-')
            if not self.model_name:
                continue
            path = os.path.join(self.project_root, self.model_name, fname)
            if fname == "disas.txt":
                try:
                    viewer = self.query_one(f"#model-editor-{safe_fname}", DiskVirtualViewer)
                    viewer.filepath = path
                    viewer.reload()
                except Exception:
                    pass
            else:
                try:
                    ta = self.query_one(f"#model-editor-{safe_fname}", TextArea)
                    if os.path.exists(path):
                        with open(path, 'r', encoding='utf-8', errors='replace') as f:
                            ta.text = f.read()
                    else:
                        ta.text = ""
                except Exception:
                    pass

    def on_mount(self) -> None:
        log = self.query_one("#output-log", TextArea)
        log.text = "RSC IDE Ready. Press Ctrl+O to open a workspace file.\n"
        config, config_file = get_config()
        if not config.get("MODEL"):
            def set_model(selected_model: str):
                self.model_name = selected_model
                config["MODEL"] = selected_model
                save_config(config, config_file)
                self.reload_model_files()
            self.app.push_screen(ModelSelectModal(current_model=None), set_model)
        else:
            self.model_name = config.get("MODEL")
            self.reload_model_files()

        self.background_check_update()

        # Populate workspace
        try:
            tree = self.query_one("#workspace-tree", Tree)
            tree.root.expand()
            folders = ["rsc_ropchain", "asm_ropchain"]
            for folder in folders:
                folder_path = os.path.join(self.project_root, folder)
                os.makedirs(folder_path, exist_ok=True)
                node = tree.root.add(folder, expand=True)
                node.data = folder_path
                
                files = sorted([f for f in os.listdir(folder_path) if f.endswith(('.rsc', '.py', '.asm'))])
                for f in files:
                    leaf = node.add_leaf(f)
                    leaf.data = os.path.join(folder_path, f)
        except Exception:
            pass
    def set_update_status(self, status: str):
        self.update_status = status

    @work(thread=True)
    def background_check_update(self, auto_mode=True):
        has_update, remote_hash, has_uncommitted = check_update_available(auto_mode=auto_mode)
        if has_update:
            self.app.call_from_thread(self.set_update_status, "Update Available!")
            self.app.call_from_thread(self.app.push_screen, UpdateModal(remote_hash, has_uncommitted))
        else:
            self.app.call_from_thread(self.set_update_status, "Up to date")
            if not auto_mode:
                self.app.call_from_thread(self.notify, "You are already on the latest version.")

    def action_change_model(self):
        def set_model(selected_model: str):
            self.model_name = selected_model
            config, config_file = get_config()
            config["MODEL"] = selected_model
            save_config(config, config_file)
            self.reload_model_files()
        self.app.push_screen(ModelSelectModal(self.model_name), set_model)

    def action_check_update(self):
        self.background_check_update(auto_mode=False)

    def show_context_menu(self, x: int, y: int) -> None:
        if hasattr(self, '_ctx_screen') and self._ctx_screen in self.screen_stack:
            self.pop_screen()
            self._ctx_screen = None
            
        ctx = ContextMenu(x, y)
        self._ctx_screen = ctx
        self.push_screen(ctx, self._on_ctx_done)

    def _on_ctx_done(self, result: str | None) -> None:
        self._ctx_screen = None
        self.handle_context_menu_action(result)

    def handle_context_menu_action(self, action_id: str | None) -> None:
        if not action_id or action_id == "ctx-cancel": return
        editor = self.query_one("#editor-area", TextArea)
        focused = self.focused if isinstance(self.focused, TextArea) else editor
        
        if action_id == "ctx-undo":
            if hasattr(focused, "action_undo"): focused.action_undo()
        elif action_id == "ctx-copy":
            self.action_editor_copy()
        elif action_id == "ctx-cut":
            self.action_editor_cut()
        elif action_id == "ctx-paste":
            self.action_editor_paste()
        elif action_id == "ctx-save":
            self.action_save_files()
        elif action_id == "ctx-run":
            self.action_compile_run()
        elif action_id == "ctx-search":
            self.action_toggle_search()
        elif action_id == "ctx-workspace":
            self.action_goto_workspace()

    @on(events.Resize)
    def on_resize(self, event: events.Resize) -> None:
        try:
            if event.size.width < 100:
                self.is_mobile = True
                self.query_one(Footer).display = False
                self.query_one("#mobile-tabs").display = True
                self.query_one("#sidebar").display = False
                self.query_one("#right-pane").display = False
                self.query_one("#activity-bar").display = False
                
                try:
                    self.query_one("#left-resizer").display = False
                    self.query_one("#right-resizer").display = False
                except Exception:
                    pass
                
                if not hasattr(self, '_mobile_init'):
                    self.set_mobile_tab("workspace")
                    self._mobile_init = True
            else:
                self.is_mobile = False
                self.query_one(Footer).display = True
                self.query_one("#mobile-tabs").display = False
                
                if not hasattr(self, '_desktop_init'):
                    self.query_one("#workspace-pane").display = True
                    self.query_one("#sidebar").display = False
                    self._desktop_init = True
                
                self.query_one("#activity-bar").display = True
                self._update_activity_bar()
                
                sidebar = self.query_one("#sidebar")
                sidebar.styles.width = "40"
                
                workspace = self.query_one("#workspace-pane")
                workspace.styles.width = "40"
                
                editor = self.query_one("#editor-container")
                editor.display = True
                editor.styles.width = "1fr"
                
                rpane = self.query_one("#right-pane")
                rpane.display = True
                rpane.styles.width = "35%"
                
                try:
                    self.query_one("#left-resizer").display = self.query_one("#workspace-pane").display or self.query_one("#sidebar").display
                    self.query_one("#right-resizer").display = True
                except Exception:
                    pass
                
                mtabs = self.query_one("#model-tabs")
                mtabs.display = True
                mtabs.styles.height = "50%"
                
                outlog = self.query_one("#output-log")
                outlog.display = True
                outlog.styles.height = "1fr"
        except Exception:
            pass

    @on(Button.Pressed)
    def handle_toolbar_buttons(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "tb-run":
            self.action_compile_run()
        elif btn_id == "tb-save":
            self.action_save_files()
        elif btn_id == "tb-find":
            self.action_toggle_search()
        elif btn_id == "tb-copy":
            self.action_editor_copy()
        elif btn_id == "tb-paste":
            self.action_editor_paste()
        elif btn_id == "tb-undo":
            self.action_editor_undo()
        elif btn_id == "tb-redo":
            self.action_editor_redo()

    def set_mobile_tab(self, tab: str):
        for btn in self.query(".mtab-btn"):
            btn.remove_class("-active")
        self.query_one(f"#mtab-{tab}", Button).add_class("-active")
            
        sidebar = self.query_one("#sidebar")
        workspace = self.query_one("#workspace-pane")
        editor = self.query_one("#editor-container")
        rpane = self.query_one("#right-pane")
        
        for pane in (sidebar, workspace, editor, rpane):
            pane.styles.width = "1fr"
            pane.display = False
            
        try:
            self.query_one("#left-resizer").display = False
            self.query_one("#right-resizer").display = False
        except Exception:
            pass
            
        if tab == "find":
            sidebar.display = True
        elif tab == "workspace":
            workspace.display = True
        elif tab == "editor":
            editor.display = True
        elif tab == "models":
            rpane.display = True
            self.query_one("#model-tabs").display = True
            self.query_one("#model-tabs").styles.height = "1fr"
            self.query_one("#output-log").display = False
        elif tab == "output":
            rpane.display = True
            self.query_one("#model-tabs").display = False
            self.query_one("#output-log").display = True
            self.query_one("#output-log").styles.height = "1fr"

    def action_goto_workspace(self) -> None:
        workspace = self.query_one("#workspace-pane")
        sidebar = self.query_one("#sidebar")
        if self.is_mobile:
            self.set_mobile_tab("workspace")
            return
        
        if workspace.display:
            workspace.display = False
            try: self.query_one("#left-resizer").display = False
            except Exception: pass
            self.query_one("#editor-area").focus()
        else:
            sidebar.display = False
            workspace.display = True
            try: self.query_one("#left-resizer").display = True
            except Exception: pass
            self.query_one("#workspace-tree").focus()
        self._update_activity_bar()
        
    def action_toggle_search(self) -> None:
        sidebar = self.query_one("#sidebar")
        workspace = self.query_one("#workspace-pane")
        if self.is_mobile:
            self.set_mobile_tab("find")
            self.query_one("#global-search-input", Input).focus()
            return
            
        if sidebar.display:
            sidebar.display = False
            try: self.query_one("#left-resizer").display = False
            except Exception: pass
            self.query_one("#editor-area").focus()
        else:
            workspace.display = False
            sidebar.display = True
            try: self.query_one("#left-resizer").display = True
            except Exception: pass
            self.query_one("#global-search-input", Input).focus()
        self._update_activity_bar()

    def _update_activity_bar(self):
        if self.is_mobile: return
        try:
            for btn in self.query(".activity-btn"):
                btn.remove_class("-active")
            if self.query_one("#workspace-pane").display:
                self.query_one("#act-workspace", Button).add_class("-active")
            elif self.query_one("#sidebar").display:
                self.query_one("#act-find", Button).add_class("-active")
        except:
            pass

    
    def _get_search_params(self):
        query = self.query_one("#global-search-input", Input).value
        replacement = self.query_one("#global-replace-input", Input).value
        is_regex = self.query_one("#btn-regex", Button).has_class("-active")
        is_case = self.query_one("#btn-case", Button).has_class("-active")
        return query, replacement, is_regex, is_case

    def perform_search(self):
        query, _, is_regex, is_case = self._get_search_params()
        results_view = self.query_one("#search-results", ListView)
        results_view.clear()
        
        if not query:
            return
        
        flags = 0 if is_case else re.IGNORECASE
        
        def match_line(line: str) -> bool:
            if is_regex:
                try:
                    return bool(re.search(query, line, flags))
                except:
                    return False
            else:
                if is_case:
                    return query in line
                else:
                    return query.lower() in line.lower()
                    
        def format_snippet(line: str) -> str:
            from rich.markup import escape
            pattern = query if is_regex else re.escape(query)
            try:
                match = re.search(pattern, line, flags)
            except:
                match = None
                
            if not match:
                return f"[gray]{escape(line.strip()[:40])}[/gray]"
                
            start, end = match.span()
            ctx_start = max(0, start - 20)
            ctx_end = min(len(line), end + 20)
            
            prefix = escape(line[ctx_start:start])
            if ctx_start > 0: prefix = "..." + prefix
            
            match_str = escape(line[start:end])
            
            suffix = escape(line[end:ctx_end])
            if ctx_end < len(line): suffix += "..."
            
            return f"[gray]{prefix}[/gray][bold yellow]{match_str}[/bold yellow][gray]{suffix}[/gray]"
                    
        MAX_RESULTS = 100
        count = 0
        
        # Update all TextAreas to highlight search term
        for ta in self.query(CtxTextArea):
            ta.update_search(query, is_regex, is_case)
        
        
        editor = self.query_one("#editor-area", TextArea)
        if self.current_filepath:
            fname = os.path.basename(self.current_filepath)
            lines = editor.text.split('\n')
            for i, line in enumerate(lines):
                if match_line(line):
                    snippet = format_snippet(line)
                    lbl = Label(f"📄 [b]{fname}[/b]:{i+1}\n  {snippet}")
                    results_view.append(SearchResultItem(lbl, target="main", line=i, match_text=line))
                    count += 1
                    if count >= MAX_RESULTS: break
                    
        
        for mname in self.model_files:
            if count >= MAX_RESULTS: break
            path = os.path.join(self.project_root, self.model_name, mname)
            if not os.path.exists(path): continue
            
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                for i, line in enumerate(f):
                    if match_line(line):
                        snippet = format_snippet(line)
                        lbl = Label(f"📦 [b]{mname}[/b]:{i+1}\n  {snippet}")
                        results_view.append(SearchResultItem(lbl, target=mname, line=i, match_text=line))
                        count += 1
                        if count >= MAX_RESULTS: break

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "global-search-input":
            self.perform_search()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id in ("act-cmd", "mtab-cmd"):
            self.action_command_palette()
        elif btn_id == "act-workspace":
            self.action_goto_workspace()
        elif btn_id == "act-find":
            self.action_toggle_search()
        elif btn_id == "act-run":
            self.action_compile_run()
        elif btn_id and btn_id.startswith("mtab-"):
            self.set_mobile_tab(btn_id.split("-")[1])
        elif btn_id == "btn-case" or btn_id == "btn-regex":
            event.button.toggle_class("-active")
            self.perform_search()
        elif btn_id == "btn-replace":
            self.action_replace_single()
        elif btn_id == "btn-replace-all":
            self.action_replace_all()

    def get_replacement_string(self, text: str, query: str, replacement: str, is_regex: bool, is_case: bool) -> str:
        if is_regex:
            flags = 0 if is_case else re.IGNORECASE
            try:
                return re.sub(query, replacement, text, flags=flags)
            except:
                return text
        else:
            if is_case:
                return text.replace(query, replacement)
            else:
                escaped_query = re.escape(query)
                return re.sub(escaped_query, replacement, text, flags=re.IGNORECASE)

    def action_replace_single(self):
        results_view = self.query_one("#search-results", ListView)
        if not results_view.highlighted_child:
            log = self.query_one("#output-log", TextArea)
            log.text += "[bold yellow]Please select a result in the list first![/bold yellow]\n"
            return
            
        item = results_view.highlighted_child
        if not isinstance(item, SearchResultItem): return
        
        query, replacement, is_regex, is_case = self._get_search_params()
        
        target = item.target_file
        line_num = item.line_num
        
        ta = None
        if target == "main":
            ta = self.query_one("#editor-area", TextArea)
            lines = ta.text.split('\n')
            if 0 <= line_num < len(lines):
                lines[line_num] = self.get_replacement_string(lines[line_num], query, replacement, is_regex, is_case)
                ta.text = "\n".join(lines)
        else:
            self.query_one("#output-log", TextArea).text += "[bold yellow]Cannot replace in Model files (Read-Only)[/bold yellow]\n"
            return
            
        self.perform_search()

    def action_replace_all(self):
        query, replacement, is_regex, is_case = self._get_search_params()
        
        if not query: return
        
        if self.current_filepath:
            ta = self.query_one("#editor-area", TextArea)
            ta.text = self.get_replacement_string(ta.text, query, replacement, is_regex, is_case)
            
        self.query_one("#output-log", TextArea).text += "[bold cyan]Replace All completed on main editor.[/bold cyan]\n"
        self.perform_search()

    def jump_to_line(self, target: str, line_num: int):
        if target == "main":
            if self.is_mobile: self.set_mobile_tab("editor")
            editor = self.query_one("#editor-area", TextArea)
            editor.move_cursor((line_num, 0))
            editor.focus()
        else:
            if self.is_mobile: self.set_mobile_tab("models")
            safe_fname = target.replace('.', '-')
            tabs = self.query_one("#model-tabs", TabbedContent)
            tabs.active = f"tab-{safe_fname}"
            if target == "disas.txt":
                viewer = self.query_one(f"#model-editor-{safe_fname}", DiskVirtualViewer)
                viewer.scroll_to_line(line_num)
                viewer.focus()
            else:
                editor = self.query_one(f"#model-editor-{safe_fname}", TextArea)
                editor.move_cursor((line_num, 0))
                editor.focus()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, SearchResultItem):
            self.jump_to_line(item.target_file, item.line_num)
        
    def action_save_files(self) -> None:
        log = self.query_one("#output-log", TextArea)
        
        # Build list of (filepath, textarea_id)
        files_to_save = []
        if self.current_filepath:
            files_to_save.append((self.current_filepath, "#editor-area"))
            
        if self.model_name:
            for fname in self.model_files:
                if fname != "disas.txt":
                    safe_fname = fname.replace('.', '-')
                    path = os.path.join(self.project_root, self.model_name, fname)
                    files_to_save.append((path, f"#model-editor-{safe_fname}"))
                    
        for path, ta_id in files_to_save:
            try:
                ta = self.query_one(ta_id, TextArea)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(ta.text)
            except Exception as e:
                log.text += f"Error saving {os.path.basename(path)}: {e}\n"
        
        log.text += "> Files saved successfully.\n"

    def action_compile_run(self) -> None:
        self.action_save_files()
        self.compile_current_file()

    def action_editor_copy(self) -> None:
        focused = self.screen.focused
        if hasattr(focused, "selected_text"):
            text = focused.selected_text
            if text:
                try:
                    import pyperclip
                    pyperclip.copy(text)
                except Exception:
                    pass
        if hasattr(focused, "action_copy"):
            focused.action_copy()
            self.notify("Copied to system clipboard")
        else:
            self.notify("Cannot copy from here", severity="warning")

    def action_editor_cut(self) -> None:
        self.action_editor_copy()
        if hasattr(self.focused, "action_delete_left"):
            self.focused.action_delete_left()

    def action_editor_paste(self) -> None:
        focused = self.screen.focused
        if hasattr(focused, "action_paste") and not getattr(focused, "read_only", False):
            try:
                import pyperclip
                text = pyperclip.paste()
                if text:
                    if hasattr(focused, "replace") and hasattr(focused, "selection"):
                        focused.replace(text, focused.selection.start, focused.selection.end)
                    elif hasattr(focused, "insert_text_at_cursor"):
                        focused.insert_text_at_cursor(text)
                    else:
                        focused.action_paste()
                    self.notify("Pasted from system clipboard")
                    return
            except Exception:
                pass
            focused.action_paste()
            self.notify("Pasted from internal clipboard")
        else:
            self.notify("Cannot paste here", severity="warning")

    def action_editor_undo(self) -> None:
        focused = self.screen.focused
        if hasattr(focused, "action_undo") and not getattr(focused, "read_only", False):
            focused.action_undo()

    def action_editor_redo(self) -> None:
        focused = self.screen.focused
        if hasattr(focused, "action_redo") and not getattr(focused, "read_only", False):
            focused.action_redo()

    def compile_current_file(self) -> None:
        if not self.current_filepath:
            log = self.query_one("#output-log", TextArea)
            log.text += "Please open a file first (Ctrl+O)!\n"
            if self.is_mobile: self.set_mobile_tab("output")
            return
            
        self.action_save_files()
        
        log = self.query_one("#output-log", TextArea)
        editor = self.query_one("#editor-area", RscTextArea)
        
        out_buffer = f"> Compiling {os.path.basename(self.current_filepath)}...\n"
        log.text = out_buffer
        
        rac_path = os.path.join(self.project_root, "rac.py")
        cmd = [sys.executable, rac_path, self.model_name, self.current_filepath]
        if os.environ.get("RAC_SAFE_MODE") == "1":
            cmd.append("--safe")
        
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            out = res.stdout + "\n" + res.stderr
            error_found = False
            
            for line in out.split('\n'):
                if not line.strip(): continue
                if "error" in line.lower() and "-->" in line:
                    out_buffer += line + "\n"
                    m = re.search(r'-->\s*([^:]+):(\d+)', line)
                    if m:
                        e_file = m.group(1).strip()
                        e_line = int(m.group(2))
                        if os.path.basename(self.current_filepath) in e_file or self.current_filepath.endswith(e_file):
                            target_line = max(0, e_line - 1)
                            self.jump_to_line("main", target_line)
                            error_found = True
                else:
                    out_buffer += line + "\n"
                    
            if not error_found and res.returncode == 0:
                out_buffer += "> Compile Successful!\n"
            
            log.text = out_buffer
            
            self.reload_model_files()

        except Exception as e:
            log.text += f"Compiler execution failed: {e}\n"
            if self.is_mobile: 
                self.set_mobile_tab("output")
            else:
                self.query_one("#output-log").focus()

    @on(Tree.NodeSelected, "#workspace-tree")
    def on_workspace_node_selected(self, event: Tree.NodeSelected) -> None:
        path = event.node.data
        if path and not os.path.isdir(path):
            self.open_file(path)
            if not self.is_mobile:
                self.query_one("#editor-area").focus()

    def open_file(self, path: str) -> None:
        self.current_filepath = path
        editor = self.query_one("#editor-area", RscTextArea)
        
        editor.language = None
        editor._use_rsc_highlight = True
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            editor.load_text(content)
            self.query_one("#ws-title", Label).update(f"Workspace - {os.path.basename(path)}")
            if self.is_mobile:
                self.set_mobile_tab("editor")
        except Exception as e:
            self.query_one("#output-log", TextArea).text += f"Failed to read file: {e}\n"

    @on(TabbedContent.TabActivated)
    def handle_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        if event.pane and event.pane.id and event.pane.id.startswith("tab-"):
            for viewer in event.pane.query(DiskVirtualViewer):
                viewer.reload()


if __name__ == "__main__":
    app = RSC_IDE()
    app.run()
