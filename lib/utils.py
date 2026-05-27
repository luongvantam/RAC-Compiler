import sys
import re

def default_note(st):
    ''' Print st to stderr. Used for additional information (note, warning) '''
    sys.stderr.write(st)

note = default_note

def to_lowercase(s):
    return s.lower()

def canonicalize(st):
    st = st.strip()
    parts = re.split(r'(".*?")', st)  
    for i in range(len(parts)):
        if i % 2 == 0:
            parts[i] = re.sub(r' *([^a-z0-9]) *', r'\1', parts[i])
    return ''.join(parts)

def del_inline_comment(line):
    return (line + '#')[:line.find('#')].rstrip()