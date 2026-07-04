"""Herf conversion engine.

Converts InPage proprietary byte-pair encoded text to standard Unicode,
and reports every byte code it could not map instead of guessing.
"""

import re
from .mapping import ITU_RULES

MARKER = "\u0004"

# cp1252 leaves these byte positions undefined; fall back to raw Latin-1
# codepoints so mapping keys like \x04\x81 (alif) resolve correctly.
_CP1252_UNDEFINED = {0x81, 0x8D, 0x8F, 0x90, 0x9D}

_BYTE_TABLE = {}
for _b in range(256):
    if _b in _CP1252_UNDEFINED:
        _BYTE_TABLE[_b] = chr(_b)
    else:
        _BYTE_TABLE[_b] = bytes([_b]).decode("cp1252")


def decode_bytes(raw: bytes) -> str:
    """Decode raw file bytes into the intermediate cp1252-based text form."""
    return "".join(_BYTE_TABLE[b] for b in raw)


def convert(text: str, user_mapping: dict | None = None,
            latin_digits: bool = False, strip_kashida: bool = False):
    """Convert intermediate text to Unicode.

    Rules are applied IN ORDER (combination sequences before single
    codes), matching the ltrc reference converter. User-supplied
    mappings are applied first so they take precedence.

    Returns (unicode_text, report) where report lists every marker+byte
    pair not covered by any rule: {code, char, count, contexts}.
    Unmapped pairs stay in the output untouched — nothing is guessed.
    """
    if user_mapping:
        for k in sorted(user_mapping.keys(), key=len, reverse=True):
            if k in text:
                text = text.replace(k, user_mapping[k])

    for k, v in ITU_RULES:
        if k in text:
            text = text.replace(k, v)

    # Collect unmapped marker pairs BEFORE cleanup, with context.
    report = {}
    for m in re.finditer(MARKER + r"(?![ \r\n])(.)", text):
        ch = m.group(1)
        code = f"0x04 0x{ord(ch):02X}"
        entry = report.setdefault(code, {"code": code, "char": ch,
                                         "count": 0, "contexts": []})
        entry["count"] += 1
        if len(entry["contexts"]) < 5:
            s = max(0, m.start() - 25)
            ctx = text[s:m.end() + 25].replace(MARKER, " ")
            ctx = re.sub(r"\s+", " ", ctx).strip()
            entry["contexts"].append(ctx)

    # Remaining lone markers are InPage word-space markers.
    text = text.replace(MARKER, " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\r?\n *", "\n", text)
    text = text.strip()

    if latin_digits:
        text = text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
    if strip_kashida:
        text = text.replace("\u0640", "")

    return text, sorted(report.values(), key=lambda e: -e["count"])


def convert_bytes(raw: bytes, **kwargs):
    return convert(decode_bytes(raw), **kwargs)
