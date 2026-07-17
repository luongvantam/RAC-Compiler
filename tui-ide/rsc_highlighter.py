"""
RSC / ASM syntax highlighter for the TUI IDE.
Mirrors the rules from .vscode/extensions/rsc-syntax/syntaxes/rsc.tmLanguage.json.

Usage:
    from rsc_highlighter import highlight_rsc_line
    spans = highlight_rsc_line(text)  # list of (start, end, rich.style.Style)
"""
import re
import json
import os
from functools import lru_cache
from rich.style import Style

# ----------------------------------------------------------------------
# 1. Scope/Style Mappings
# ----------------------------------------------------------------------
S_COMMENT    = Style(color="#6272a4", italic=True)   # Comments
S_STRING     = Style(color="#f1fa8c")                # Strings
S_KEYWORD    = Style(color="#ff79c6", bold=True)     # Control flow
S_KEYWORD_OP = Style(color="#ff79c6")                # in, and, or, not
S_STORAGE    = Style(color="#ff79c6", bold=True)     # var, reg, loop, repeat, str
S_NUMBER     = Style(color="#bd93f9")                # Numbers (dec, hex)
S_HEX_BYTE   = Style(color="#bd93f9", bold=True)     # Hex bytes (FF, 0A)
S_REGISTER   = Style(color="#50fa7b")                # Registers
S_FUNCTION   = Style(color="#50fa7b", bold=True)     # Function names
S_BUILTIN    = Style(color="#8be9fd")                # Built-in functions
S_LABEL      = Style(color="#f8f8f2", underline=True)# Labels definition
S_LABEL_REF  = Style(color="#ffb86c")                # Label references
S_DIRECTIVE  = Style(color="#ff79c6", bold=True)     # @build, @set, @section
S_SUPPORT    = Style(color="#8be9fd")                # emu.*, line.*, output.*
S_OPERATOR   = Style(color="#ff79c6")                # ==, !=, +, -
S_PUNCT      = Style(color="#f8f8f2")                # [, ], {, }, (, )
S_KEY        = Style(color="#ffb86c", bold=True)     # KEY_xxx
S_DEFAULT    = Style(color="#f8f8f2")                # Normal text

# ----------------------------------------------------------------------
# 2. Regex Patterns (Loaded from JSON)
# ----------------------------------------------------------------------
_PATTERNS: list[tuple[re.Pattern, int | None, Style]] = []

STYLE_MAP = {
    "directive": S_DIRECTIVE,
    "support_variable": S_SUPPORT,
    "storage_modifier": S_STORAGE,
    "storage_type": S_STORAGE,
    "keyword": S_KEYWORD,
    "distance_helper": S_KEYWORD,
    "builtin": S_BUILTIN,
    "python_func": S_FUNCTION,
    "function_def": S_FUNCTION,
    "function_call": S_FUNCTION,
    "function_call_direct": S_FUNCTION,
    "label_def_1": S_LABEL,
    "label_def_2": S_LABEL,
    "label_ref_1": S_LABEL_REF,
    "label_ref_2": S_LABEL_REF,
    "register": S_REGISTER,
    "constant": S_KEY,
    "number_hex_array": S_HEX_BYTE,
    "number_hex": S_NUMBER,
    "number_hex_byte": S_HEX_BYTE,
    "number_dec": S_NUMBER,
    "operator": S_OPERATOR,
    "punctuation": S_PUNCT
}

def load_syntax():
    json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "libcompiler", "syntax.json")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for rule in data.get("rules", []):
            rule_id = rule.get("id")
            regex_str = rule.get("regex")
            if not rule_id or not regex_str or rule_id not in STYLE_MAP:
                continue
            flags = 0
            if rule.get("flags_py") == "IGNORECASE":
                flags |= re.IGNORECASE
            # flags_js='m' could map to re.MULTILINE if needed, but we match line by line in Python anyway
            grp = rule.get("group")
            _PATTERNS.append((re.compile(regex_str, flags), grp, STYLE_MAP[rule_id]))
    except Exception as e:
        print(f"Failed to load syntax.json: {e}")

load_syntax()


@lru_cache(maxsize=10000)
def highlight_rsc_line(text: str, in_comment: bool = False) -> tuple[list[tuple[int, int, Style]], bool]:
    """
    Returns a list of (start, end, Style) spans for the given line, and the new in_comment state.
    Spans do not overlap; earlier patterns win (priority order).
    """
    n = len(text)
    
    claimed = bytearray(n)  

    results: list[tuple[int, int, Style]] = []

    
    pos = 0
    while pos < n:
        if in_comment:
            end_idx = text.find('*/', pos)
            if end_idx != -1:
                end_comment = end_idx + 2
                results.append((pos, end_comment, S_COMMENT))
                for i in range(pos, end_comment): claimed[i] = 1
                pos = end_comment
                in_comment = False
            else:
                results.append((pos, n, S_COMMENT))
                for i in range(pos, n): claimed[i] = 1
                in_comment = True
                break
        else:
            
            next_block = text.find('/*', pos)
            next_str1 = text.find('"', pos)
            next_str2 = text.find("'", pos)
            next_line_comment = text.find('#', pos)
            
            candidates = []
            if next_block != -1: candidates.append((next_block, 'block'))
            if next_str1 != -1: candidates.append((next_str1, 'str1'))
            if next_str2 != -1: candidates.append((next_str2, 'str2'))
            if next_line_comment != -1: candidates.append((next_line_comment, 'line'))
            
            if not candidates:
                break
                
            first_idx, kind = min(candidates, key=lambda x: x[0])
            
            if kind == 'block':
                in_comment = True
                pos = first_idx
            elif kind == 'str1':
                end_idx = first_idx + 1
                while end_idx < n:
                    if text[end_idx] == '"' and text[end_idx-1] != '\\':
                        break
                    end_idx += 1
                end_idx = min(end_idx + 1, n)
                results.append((first_idx, end_idx, S_STRING))
                for i in range(first_idx, end_idx): claimed[i] = 1
                pos = end_idx
            elif kind == 'str2':
                end_idx = first_idx + 1
                while end_idx < n:
                    if text[end_idx] == "'" and text[end_idx-1] != '\\':
                        break
                    end_idx += 1
                end_idx = min(end_idx + 1, n)
                results.append((first_idx, end_idx, S_STRING))
                for i in range(first_idx, end_idx): claimed[i] = 1
                pos = end_idx
            elif kind == 'line':
                results.append((first_idx, n, S_COMMENT))
                for i in range(first_idx, n): claimed[i] = 1
                break

    for pattern, grp, style in _PATTERNS:
        for m in pattern.finditer(text):
            if grp is not None:
                try:
                    start, end = m.span(grp)
                except IndexError:
                    start, end = m.span(0)
            else:
                start, end = m.span(0)

            if start >= n or end > n:
                continue
            
            if any(claimed[start:end]):
                continue
            
            for i in range(start, end):
                claimed[i] = 1
            results.append((start, end, style))

    results.sort(key=lambda x: x[0])
    return results, in_comment


def make_segments(line_text: str, in_comment: bool = False, default_style: Style = S_DEFAULT) -> tuple[list, bool]:
    """
    Convert a plain text line + highlight spans into a list of rich Segment objects.
    """
    from rich.segment import Segment

    spans, next_in_comment = highlight_rsc_line(line_text, in_comment)
    segments = []
    pos = 0
    for start, end, style in spans:
        if pos < start:
            segments.append(Segment(line_text[pos:start], default_style))
        segments.append(Segment(line_text[start:end], style))
        pos = end
    if pos < len(line_text):
        segments.append(Segment(line_text[pos:], default_style))
    return segments, next_in_comment
