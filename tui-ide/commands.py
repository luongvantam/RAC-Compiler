from libcompiler.i18n import t
from textual.command import Provider, Hit
from textual.widgets import OptionList
from textual.screen import ModalScreen
from textual import events, on

class IDECommandProvider(Provider):
    async def discover(self):
        from textual.command import DiscoveryHit
        yield DiscoveryHit(t("cmd_open_workspace"), lambda: self.app.action_goto_workspace(), help=t("cmd_help_open_workspace"))
        yield DiscoveryHit(t("cmd_change_model"), lambda: self.app.action_change_model(), help=t("cmd_help_current_model", model=self.app.model_name))
        yield DiscoveryHit(t("cmd_update_rac"), lambda: self.app.action_check_update(), help=t("cmd_help_status", status=self.app.update_status))
        yield DiscoveryHit(t("cmd_run_compiler"), lambda: self.app.action_compile_run(), help=t("cmd_help_run_compiler"))
        yield DiscoveryHit(t("cmd_save_file"), lambda: self.app.action_save_files(), help=t("cmd_help_save_file"))
        yield DiscoveryHit(t("cmd_change_language"), lambda: self.app.action_change_language(), help=t("cmd_help_change_language"))
        
    async def search(self, query: str):
        matcher = self.matcher(query)
        
        commands = [
            ("Change Model", self.app.action_change_model, f"Current: {self.app.model_name}"),
            ("Update RAC-Compiler", self.app.action_check_update, f"Status: {self.app.update_status}"),
            ("Run Compiler", self.app.action_compile_run, "Compile the current file"),
            ("Save File", self.app.action_save_files, "Save current file"),
            ("Change Language", self.app.action_change_language, "Change IDE Language"),
        ]
        
        for name, callback, help_text in commands:
            score = matcher.match(name)
            if score > 0:
                yield Hit(score, matcher.highlight(name), callback, help=help_text)

