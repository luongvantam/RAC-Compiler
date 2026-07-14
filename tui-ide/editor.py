from libcompiler.i18n import t
from textual.widgets import TextArea
from textual.binding import Binding
from textual import events
import os
import sys
import re

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

class CtxTextArea(TextArea):
    def __init__(self, *args, **kwargs):
        self.search_query = ""
        self.search_is_regex = False
        self.search_is_case = False
        super().__init__(*args, **kwargs)

    def on_mount(self) -> None:
        import textual.widgets._text_area as t
        from rich.style import Style
        try:
            theme_name = getattr(self, "theme", "monokai")
            if not theme_name: theme_name = "monokai"
            theme = t.TextAreaTheme.get_builtin_theme(theme_name)
            if theme:
                theme.syntax_styles["search.match"] = Style(bgcolor="#ffff00", color="#000000", bold=True)
        except Exception:
            pass

    def update_search(self, query: str, is_regex: bool, is_case: bool) -> None:
        self.search_query = query
        self.search_is_regex = is_regex
        self.search_is_case = is_case
        self._line_cache.clear()
        self.refresh()

    def _build_highlight_map(self) -> None:
        super()._build_highlight_map()
        if not self.search_query:
            return
        import re
        flags = 0 if self.search_is_case else re.IGNORECASE
        pattern = self.search_query if self.search_is_regex else re.escape(self.search_query)
        try:
            compiled = re.compile(pattern, flags)
            lines = self.text.split("\n")
            for i, line in enumerate(lines):
                for match in compiled.finditer(line):
                    start, end = match.span()
                    if start != end:
                        self._highlights[i].append((start, end, "search.match"))
        except Exception:
            pass

    async def _on_mouse_down(self, event: events.MouseDown) -> None:
        if event.button == 3:
            event.prevent_default()
            event.stop()
            if hasattr(self.app, "show_context_menu"):
                self.app.show_context_menu(event.screen_x, event.screen_y)
            return
            
        if getattr(self.app, "is_mobile", False) and event.button == 1:
            if hasattr(self, "_lp_timer") and self._lp_timer is not None:
                self._lp_timer.stop()
            self._lp_pos = (event.screen_x, event.screen_y)
            def _trigger():
                self._lp_timer = None
                if hasattr(self.app, "show_context_menu"):
                    self.app.show_context_menu(self._lp_pos[0], self._lp_pos[1])
            self._lp_timer = self.set_timer(0.6, _trigger)
            
        await super()._on_mouse_down(event)

    async def _on_mouse_move(self, event: events.MouseMove) -> None:
        if hasattr(self, "_lp_timer") and self._lp_timer is not None:
            dx = event.screen_x - getattr(self, "_lp_pos", (0,0))[0]
            dy = event.screen_y - getattr(self, "_lp_pos", (0,0))[1]
            if dx*dx + dy*dy > 10:
                self._lp_timer.stop()
                self._lp_timer = None
        if hasattr(super(), "_on_mouse_move"):
            await super()._on_mouse_move(event)

    async def _on_mouse_up(self, event: events.MouseUp) -> None:
        if hasattr(self, "_lp_timer") and self._lp_timer is not None:
            self._lp_timer.stop()
            self._lp_timer = None
        if hasattr(super(), "_on_mouse_up"):
            await super()._on_mouse_up(event)

    def action_copy(self) -> None:
        super().action_copy()
        if hasattr(self.app, "notify"):
            self.app.notify(t("msg_copied_clipboard"), severity="information")

    def action_cut(self) -> None:
        super().action_cut()
        if hasattr(self.app, "notify"):
            self.app.notify(t("msg_cut_clipboard"), severity="information")

    def action_paste(self) -> None:
        super().action_paste()
        if hasattr(self.app, "notify"):
            self.app.notify(t("msg_pasted_clipboard"), severity="information")

class RscTextArea(CtxTextArea):
    """TextArea subclass with RSC/ASM syntax highlighting via regex."""

    def __init__(self, *args, **kwargs):
        self._use_rsc_highlight = False
        super().__init__(*args, **kwargs)

    def _build_highlight_map(self) -> None:
        """Override to inject RSC highlights when in rsc/asm mode."""
        
        super()._build_highlight_map()

        if not self._use_rsc_highlight or not HAS_RSC_HIGHLIGHT:
            return

        from rsc_highlighter import highlight_rsc_line
        
        SCOPE_MAP = {
            S_COMMENT:    "comment",
            S_STRING:     "string",
            S_KEYWORD:    "keyword",
            S_KEYWORD_OP: "keyword.operator",
            S_STORAGE:    "keyword",
            S_NUMBER:     "number",
            S_HEX_BYTE:   "number",
            S_REGISTER:   "variable.builtin",
            S_FUNCTION:   "function",
            S_BUILTIN:    "function.call",
            S_LABEL:      "type",
            S_LABEL_REF:  "constant.builtin",
            S_DIRECTIVE:  "keyword",
            S_SUPPORT:    "function.call",
            S_OPERATOR:   "operator",
            S_PUNCT:      "punctuation.bracket",
            S_KEY:        "constant.builtin",
        }
        lines = self.text.split("\n")
        in_comment = False
        for row, line in enumerate(lines):
            spans, in_comment = highlight_rsc_line(line, in_comment)
            for start, end, style in spans:
                tok = SCOPE_MAP.get(style, "string")
                self._highlights[row].append((start, end, tok))
        self._line_cache.clear()

