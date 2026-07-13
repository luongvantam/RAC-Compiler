from textual.command import Provider, Hit
from textual.widgets import OptionList
from textual.screen import ModalScreen
from textual import events, on

class IDECommandProvider(Provider):
    async def discover(self):
        from textual.command import DiscoveryHit
        yield DiscoveryHit("Open Workspace", lambda: self.app.action_goto_workspace(), help="Open file workspace")
        yield DiscoveryHit("Change Model", lambda: self.app.action_change_model(), help=f"Current: {self.app.model_name}")
        yield DiscoveryHit("Update RAC-Compiler", lambda: self.app.action_check_update(), help=f"Status: {self.app.update_status}")
        yield DiscoveryHit("Run Compiler", lambda: self.app.action_compile_run(), help="Compile the current file")
        yield DiscoveryHit("Save File", lambda: self.app.action_save_files(), help="Save current file")
        
    async def search(self, query: str):
        matcher = self.matcher(query)
        
        commands = [
            ("Change Model", self.app.action_change_model, f"Current: {self.app.model_name}"),
            ("Update RAC-Compiler", self.app.action_check_update, f"Status: {self.app.update_status}"),
            ("Run Compiler", self.app.action_compile_run, "Compile the current file"),
            ("Save File", self.app.action_save_files, "Save current file"),
        ]
        
        for name, callback, help_text in commands:
            score = matcher.match(name)
            if score > 0:
                yield Hit(score, matcher.highlight(name), callback, help=help_text)

