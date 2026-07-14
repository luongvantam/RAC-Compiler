import os
import json

_translations = {}
_current_lang = "en_US"

def set_language(lang_code):
    global _current_lang, _translations
    _current_lang = lang_code
    
    # Locate locales directory (one level up from libcompiler, or wherever it exists)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    locale_file = os.path.join(base_dir, "locales", f"{lang_code}.lc")
    
    if os.path.exists(locale_file):
        try:
            with open(locale_file, "r", encoding="utf-8") as f:
                _translations = json.load(f)
        except Exception:
            _translations = {}
    else:
        _translations = {}

def t(key, **kwargs):
    if key in _translations:
        val = _translations[key]
        try:
            return val.format(**kwargs)
        except KeyError:
            return val
    return key
