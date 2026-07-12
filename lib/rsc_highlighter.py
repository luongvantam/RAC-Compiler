"""
RSC / ASM syntax highlighter for the TUI IDE.
Mirrors the rules from .vscode/extensions/rsc-syntax/syntaxes/rsc.tmLanguage.json.

Usage:
    from rsc_highlighter import highlight_rsc_line
    spans = highlight_rsc_line(text)  # list of (start, end, rich.style.Style)
"""
import re
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
# 2. Regex Patterns
# ----------------------------------------------------------------------
_PATTERNS: list[tuple[re.Pattern, int | None, Style]] = []

def _add(pattern: str, style: Style, flags: int = 0, group: int | None = None):
    _PATTERNS.append((re.compile(pattern, flags), group, style))

# Directives
_add(r'^\s*(@(?:build|python))\b',          S_DIRECTIVE, group=1)
_add(r'^\s*(@(?:set|section))(\.[A-Za-z0-9_]+)', S_DIRECTIVE, group=1)

# Support variables (emu.*, etc.)
_add(r'\b(emu\.inj_file|emu\.inj_var|emu\.inj_addr|emu\.inj_adr|emu\.inj|line\.bytes|output\.file_name|output\.file)\b', S_SUPPORT)

# Specific commands that act like keywords
_add(r'\b(org|backup)\b', S_KEYWORD)

# Built-in specials
_add(r'\bdist\b', S_BUILTIN)

# Storage types
_add(r'\b(var|reg|loop|repeat|str)\b', S_STORAGE)

# Control flow
_add(r'\b(call|goto|return|at|as|org|backup|goto_er14|goto_er6)\b', S_KEYWORD)

# Function declarations
_add(r'\b(func|def)\b', S_KEYWORD)

# Logical ops
_add(r'\b(in|and|or|not)\b', S_KEYWORD_OP)

# Key constants
_add(r'\bKEY_[A-Z0-9_]+\b', S_KEY)

# hex keyword
_add(r'\bhex\b', S_KEYWORD)

# Hex bytes array (after hex keyword) or standalone hex bytes (e.g., FF 0A)
_add(r'(?<=\bhex\s)\s*(?:[0-9A-Fa-f]{2}\s*)+', S_HEX_BYTE)  
_add(r'\b[0-9A-Fa-f]{2}\b', S_HEX_BYTE)  

# Hex numbers (0x...)
_add(r'\b0x[0-9A-Fa-f]+\b', S_NUMBER)

# Decimal numbers
_add(r'\b\d+\b', S_NUMBER)

# Registers
_add(r'\b(?:[erxq]r[0-9]{1,2}|r[0-9]{1,2}|sp|pc|ea)\b', S_REGISTER, re.IGNORECASE)

# Builtin functions
_add(r'\b(?:adr|adr_of|adr_arith|eval|calc|sizeof|pr_length|fill|align|pad|pad_abs|pr_org|pr_backup)\b', S_BUILTIN)

# Function Definitions (capture name)
_add(r'\b(func|def)\s+([A-Za-z_][A-Za-z0-9_]*)\b', S_FUNCTION, group=2)

# Function Calls (capture name)
_add(r'\b(call)\s+([A-Za-z_][A-Za-z0-9_]*)\b', S_FUNCTION, group=2)

# Labels (definition ending in colon)
_add(r'^\s*[A-Za-z_][A-Za-z0-9_]*:', S_LABEL)

# Label (via lbl keyword)
_add(r'\blbl\s+[A-Za-z_][A-Za-z0-9_]*\b', S_LABEL)

# Label References
_add(r'\b(goto)\s+([A-Za-z_][A-Za-z0-9_]*)\b', S_LABEL_REF, group=2)

# Operators
_add(r'==|!=|<=|>=|[=+\-*/%<>]', S_OPERATOR)

# Punctuation
_add(r'[,;:]', S_PUNCT)
_add(r'[(){}\[\]]', S_PUNCT)


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
