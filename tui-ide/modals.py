from textual import work
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Label, ListView, ListItem, OptionList, Input, RichLog
from textual.containers import Horizontal, Vertical
from textual import events, on
import subprocess, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from check_update import check_update_available, perform_update, get_config, save_config
from libcompiler.i18n import t

class UpdateModal(ModalScreen):
    CSS = """
    UpdateModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.6);
    }
    #update-dialog {
        padding: 1 2;
        width: 60;
        height: auto;
        border: ascii $foreground;
        background: $surface;
    }
    #update-buttons {
        margin-top: 1;
        align: center middle;
        height: auto;
    }
    #update-log {
        display: none;
        margin-top: 1;
        background: $surface;
        border: ascii $foreground;
    }
    .close-btn {
        width: 3;
        min-width: 3;
        height: 1;
        border: none;
        background: transparent;
        color: $error;
        content-align: center middle;
        dock: right;
    }
    .close-btn:hover {
        background: $error;
        color: white;
    }
    """

    def __init__(self, remote_hash: str, has_uncommitted: bool):
        super().__init__()
        self.remote_hash = remote_hash
        self.has_uncommitted = has_uncommitted

    def compose(self) -> ComposeResult:
        with Vertical(id="update-dialog"):
            yield Button("X", id="btn-close", classes="close-btn")
            yield Label(t("upd_available"))
            yield Label(t("upd_hash", hash=self.remote_hash[:7]))
            if self.has_uncommitted:
                yield Label(t("upd_warn"))
            yield Label(t("upd_prompt"))
            
            with Horizontal(id="update-buttons"):
                yield Button(t("upd_btn_update"), id="btn-update", variant="primary")
                if self.has_uncommitted:
                    yield Button(t("upd_btn_force"), id="btn-force-update", variant="error")
                yield Button(t("upd_btn_skip"), id="btn-skip", variant="primary")
                
            yield RichLog(id="update-log", markup=False, wrap=True)

    @on(Button.Pressed)
    def handle_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-close":
            self.app.pop_screen()
            return
        if btn_id in ("btn-skip"):
            config, config_file = get_config()
            if config.get("UPDATE_SKIP_HASH") != self.remote_hash:
                config["UPDATE_SKIP_HASH"] = self.remote_hash
                self.app.notify(t("upd_msg_skip"))
            else:
                self.app.notify(t("upd_msg_close"))
            config["UPDATE_LAST_CHECK"] = str(time.time())
            save_config(config, config_file)
            self.app.pop_screen()
        elif btn_id in ("btn-update", "btn-force-update"):
            force = (btn_id == "btn-force-update")
            for btn in self.query(Button):
                btn.disabled = True
            log = self.query_one("#update-log", RichLog)
            log.display = True
            log.styles.min_height = 8
            log.write(t("upd_log_start"))
            self.do_update(force)

    @work(thread=True)
    def do_update(self, force: bool) -> None:
        def log_cb(msg):
            self.app.call_from_thread(self.query_one("#update-log", RichLog).write, msg)
            
        success = perform_update(self.remote_hash, force, log_callback=log_cb)
        if success:
            log_cb(t("upd_log_success"))
            time.sleep(1.5)
            self.app.call_from_thread(sys.exit, 3)
        else:
            log_cb(t("upd_log_fail"))
            self.app.call_from_thread(self.enable_skip_only)
            
    def enable_skip_only(self):
        for btn in self.query(Button):
            if btn.id == "btn-skip":
                btn.disabled = False
                btn.label = t("upd_btn_close")
            else:
                btn.display = False

class ModelSelectModal(ModalScreen[str]):
    CSS = """
    ModelSelectModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.6);
    }
    #ms-dialog {
        padding: 1 2;
        width: 60;
        height: auto;
        border: ascii $foreground;
        background: $surface;
    }
    #ms-input {
        margin: 1 0;
    }
    #ms-buttons {
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    .close-btn {
        width: 3;
        min-width: 3;
        height: 1;
        border: none;
        background: transparent;
        color: $error;
        content-align: center middle;
        dock: right;
    }
    .close-btn:hover {
        background: $error;
        color: white;
    }
    """

    def __init__(self, current_model: str | None = None):
        super().__init__()
        self.current_model = current_model or "580vnx"

    def compose(self) -> ComposeResult:
        with Vertical(id="ms-dialog"):
            yield Button("X", id="btn-close", classes="close-btn")
            yield Label(t("ms_prompt"))
            yield Input(value=self.current_model, placeholder=t("ms_placeholder"), id="ms-input")
            with Horizontal(id="ms-buttons"):
                yield Button(t("ms_confirm"), id="ms-confirm", variant="primary")
            yield Label("", id="ms-error")

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-close":
            self.dismiss(self.current_model)
            return
            
        if event.button.id != "ms-confirm":
            return
        self.confirm_model()

    @on(Input.Submitted, "#ms-input")
    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.confirm_model()
        
    def confirm_model(self):
        val = self.query_one("#ms-input", Input).value.strip()
        if not val:
            self.query_one("#ms-error", Label).update(t("ms_err_empty"))
            return
        if not os.path.isdir(os.path.join(self.app.project_root, val)):
            self.query_one("#ms-error", Label).update(t("ms_err_notfound", val=val))
            return
        self.dismiss(val)


class ContextMenu(ModalScreen[str]):
    CSS = """
    ContextMenu { align: left top; background: transparent; }
    #menu-container { width: 20; height: auto; border: solid $primary; background: $surface; padding: 0; layer: top; }
    .menu-btn { width: 100%; border: none; height: 1; min-height: 1; content-align: left middle; padding-left: 1; background: transparent; }
    .menu-btn:hover { background: $accent; }
    """
    def __init__(self, x: int, y: int):
        super().__init__()
        self.x = x
        self.y = y

    def compose(self) -> ComposeResult:
        with Vertical(id="menu-container"):
            yield Button(t("ctx_undo"), id="ctx-undo", classes="menu-btn")
            yield Button(t("ctx_copy"), id="ctx-copy", classes="menu-btn")
            yield Button(t("ctx_cut"), id="ctx-cut", classes="menu-btn")
            yield Button(t("ctx_paste"), id="ctx-paste", classes="menu-btn")
            yield Button(t("ctx_save"), id="ctx-save", classes="menu-btn")
            yield Button(t("ctx_run"), id="ctx-run", classes="menu-btn")
            yield Button(t("ctx_search"), id="ctx-search", classes="menu-btn")
            yield Button(t("ctx_workspace"), id="ctx-workspace", classes="menu-btn")

    def on_mount(self) -> None:
        
        container = self.query_one("#menu-container")
        container.styles.offset = (self.x, self.y)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        self.dismiss(event.button.id)
        
    def on_click(self, event: events.Click) -> None:
        if event.widget == self:
            self.dismiss(None)





class LanguageSelectModal(ModalScreen[str]):
    CSS = """
    LanguageSelectModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.6);
    }
    #lang-dialog {
        padding: 1 2;
        width: 60;
        height: auto;
        border: ascii $foreground;
        background: $surface;
    }
    .close-btn {
        width: 3;
        min-width: 3;
        height: 1;
        border: none;
        background: transparent;
        color: $error;
        content-align: center middle;
        dock: right;
    }
    .close-btn:hover {
        background: $error;
        color: white;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="lang-dialog"):
            yield Button("X", id="btn-close", classes="close-btn")
            yield Label(t("ide_language") + ":")
            
            yield OptionList(
                "English (en_US)",
                "Tiếng Việt (vi_VN)",
                "中文 (zh_CN)",
                id="lang-list"
            )

    @on(Button.Pressed, "#btn-close")
    def on_button_pressed(self) -> None:
        self.dismiss(None)

    @on(OptionList.OptionSelected, "#lang-list")
    def on_option_selected(self, event: OptionList.OptionSelected) -> None:
        lang_map = {
            0: "en_US",
            1: "vi_VN",
            2: "zh_CN"
        }
        self.dismiss(lang_map.get(event.option_index, "en_US"))
