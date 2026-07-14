from libcompiler.i18n import t
from textual.binding import Binding
from textual.widgets import ListItem, Label, ListView
from textual.containers import Horizontal
from textual.scroll_view import ScrollView
from textual.strip import Strip
from textual.geometry import Size
from rich.segment import Segment
from rich.style import Style
from textual import events, on
import os

try:
    from rsc_highlighter import make_segments
    HAS_RSC_HIGHLIGHT = True
except ImportError:
    HAS_RSC_HIGHLIGHT = False

class SearchResultItem(ListItem):
    def __init__(self, label: Label, target: str, line: int, match_text: str):
        super().__init__(label)
        self.target_file = target
        self.line_num = line
        self.match_text = match_text



class MobileTabsContainer(Horizontal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_dragging = False
        self._start_x = 0
        self._start_scroll_x = 0

    def on_mouse_down(self, event: events.MouseDown):
        if event.button == 1:
            self._is_dragging = False
            self._start_x = event.screen_x
            self._start_scroll_x = self.scroll_offset.x

    def on_mouse_move(self, event: events.MouseMove):
        if event.button == 1 and hasattr(self, "_start_x"):
            if not self._is_dragging and abs(event.screen_x - self._start_x) > 2:
                self._is_dragging = True
                try:
                    self.capture_mouse()
                except Exception:
                    pass
            
            if self._is_dragging:
                dx = event.screen_x - self._start_x
                self.scroll_to(x=self._start_scroll_x - dx, animate=False)

    def on_mouse_up(self, event: events.MouseUp):
        if event.button == 1:
            if self._is_dragging:
                try:
                    self.release_mouse()
                except Exception:
                    pass
            self._is_dragging = False

class VerticalResizer(Label):
    def __init__(self, targets: list[str], is_right: bool = False, *args, **kwargs):
        super().__init__("", *args, **kwargs)
        self.targets = targets
        self.is_right = is_right
        self._dragging = False
        self._start_x = 0
        self._start_width = 0
        self._active_target = None

    def on_mouse_down(self, event: events.MouseDown):
        if event.button == 1:
            self.capture_mouse()
            self._dragging = True
            self._start_x = event.screen_x
            for t_id in self.targets:
                try:
                    node = self.app.query_one(f"#{t_id}")
                    if node.display:
                        self._active_target = node
                        self._start_width = node.size.width
                        break
                except Exception:
                    pass

    def on_mouse_move(self, event: events.MouseMove):
        if self._dragging and self._active_target:
            dx = event.screen_x - self._start_x
            if self.is_right:
                new_width = max(10, self._start_width - dx)
            else:
                new_width = max(10, self._start_width + dx)
            self._active_target.styles.width = new_width

    def on_mouse_up(self, event: events.MouseUp):
        if event.button == 1:
            self._dragging = False
            self._active_target = None
            try:
                self.release_mouse()
            except Exception:
                pass

class DiskVirtualViewer(ScrollView, can_focus=True):
    """A disk-backed virtualized text viewer for massive files with selection support."""
    DEFAULT_CSS = """
    DiskVirtualViewer {
        height: 1fr;
        overflow-x: auto;
        overflow-y: auto;
        background: $surface;
    }
    """
    BINDINGS = [
        Binding("up", "scroll_up", "Scroll Up", show=False),
        Binding("down", "scroll_down", "Scroll Down", show=False),
        Binding("left", "scroll_left", "Scroll Left", show=False),
        Binding("right", "scroll_right", "Scroll Right", show=False),
        Binding("pageup", "page_up", "Page Up", show=False),
        Binding("pagedown", "page_down", "Page Down", show=False),
        Binding("home", "scroll_home", "Home", show=False),
        Binding("end", "scroll_end", "End", show=False),
        Binding("ctrl+c", "copy", "Copy", show=False),
        Binding("cmd+c", "copy", "Copy", show=False),
    ]

    def __init__(self, filepath: str, **kwargs):
        super().__init__(**kwargs)
        self.filepath = filepath
        self.line_offsets = [0]
        self.max_width = 80
        self.total_lines = 0
        self.selection_start = None
        self.selection_end = None
        self.is_dragging = False

    def on_mount(self) -> None:
        self.reload()

    def reload(self) -> None:
        self.line_offsets = [0]
        self.max_width = 80
        self.selection_start = None
        self.selection_end = None
        if os.path.exists(self.filepath):
            with open(self.filepath, 'rb') as f:
                while True:
                    line = f.readline()
                    if not line: break
                    self.line_offsets.append(f.tell())
                    self.max_width = max(self.max_width, len(line) + 8)
        
        self.total_lines = max(1, len(self.line_offsets) - 1)
        self.virtual_size = Size(self.max_width, self.total_lines)
        self.refresh()

    @on(events.MouseDown)
    def _on_mouse_down(self, event: events.MouseDown):
        self.focus()
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
            
        if event.button == 1:
            try:
                self.capture_mouse()
            except:
                pass
            self.is_dragging = True
            _, scroll_y = self.scroll_offset
            scroll_x, _ = self.scroll_offset
            line_idx = int(event.y + scroll_y)
            char_idx = max(0, int(event.x + scroll_x - 7))
            self.selection_start = (line_idx, char_idx)
            self.selection_end = (line_idx, char_idx)
            self.refresh()

    @on(events.MouseMove)
    def _on_mouse_move(self, event: events.MouseMove):
        if hasattr(self, "_lp_timer") and self._lp_timer is not None:
            dx = event.screen_x - getattr(self, "_lp_pos", (0,0))[0]
            dy = event.screen_y - getattr(self, "_lp_pos", (0,0))[1]
            if dx*dx + dy*dy > 10:
                self._lp_timer.stop()
                self._lp_timer = None
                
        if self.is_dragging:
            _, scroll_y = self.scroll_offset
            scroll_x, _ = self.scroll_offset
            line_idx = int(event.y + scroll_y)
            char_idx = max(0, int(event.x + scroll_x - 7))
            line_idx = max(0, min(self.total_lines - 1, line_idx))
            self.selection_end = (line_idx, char_idx)
            self.refresh()

    @on(events.MouseUp)
    def _on_mouse_up(self, event: events.MouseUp):
        if hasattr(self, "_lp_timer") and self._lp_timer is not None:
            self._lp_timer.stop()
            self._lp_timer = None
            
        if event.button == 1:
            try:
                self.release_mouse()
            except:
                pass
            self.is_dragging = False

    def action_copy(self):
        if not self.selection_start or not self.selection_end:
            return
        
        start = self.selection_start
        end = self.selection_end
        if start > end:
            start, end = end, start
            
        start_row, start_col = start
        end_row, end_col = end
        
        lines = []
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r', encoding='utf-8', errors='replace') as f:
                for row in range(start_row, min(end_row + 1, self.total_lines)):
                    if row >= len(self.line_offsets): break
                    f.seek(self.line_offsets[row])
                    raw = f.readline().replace('\n', '').replace('\t', '    ')
                    
                    if row == start_row and row == end_row:
                        lines.append(raw[start_col:end_col])
                    elif row == start_row:
                        lines.append(raw[start_col:])
                    elif row == end_row:
                        lines.append(raw[:end_col])
                    else:
                        lines.append(raw)
                        
        text = "\n".join(lines)
        if hasattr(self.app, "copy_to_clipboard"):
            self.app.copy_to_clipboard(text)
        self.app.notify(t("msg_copied_viewer"))

    def render_line(self, y: int) -> Strip:
        _, scroll_y = self.scroll_offset
        line_idx = y + scroll_y  
        if not os.path.exists(self.filepath) or line_idx < 0 or line_idx >= self.total_lines:
            return Strip.blank(self.size.width)
            
        with open(self.filepath, 'r', encoding='utf-8', errors='replace') as f:
            f.seek(self.line_offsets[line_idx])
            raw = f.readline().replace('\n', '').replace('\t', '    ')
            
        gutter = f"{line_idx + 1:4d} │ "
        gutter_seg = Segment(gutter, Style(color="#6272a4"))
        
        is_rsc = self.filepath.endswith('.rsc') or self.filepath.endswith('.asm')
        if is_rsc and HAS_RSC_HIGHLIGHT:
            content_segs = make_segments(raw)
        else:
            content_segs = [Segment(raw, Style(color="#f8f8f2"))]
            
        all_segs = [gutter_seg] + content_segs
        strip = Strip(all_segs)
        
        if self.selection_start and self.selection_end:
            start = self.selection_start
            end = self.selection_end
            if start > end:
                start, end = end, start
                
            start_row, start_col = start
            end_row, end_col = end
            
            if start_row <= line_idx <= end_row:
                s_col = start_col + 7 if line_idx == start_row else 7
                e_col = end_col + 7 if line_idx == end_row else self.max_width + 7
                strip = strip.apply_style(Style(bgcolor="white", color="black"), s_col, e_col)
                
        return strip.crop(0, self.size.width)

    def scroll_to_line(self, line_num: int):
        self.scroll_to(y=line_num, animate=False)

