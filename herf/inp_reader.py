"""Direct reader for InPage .INP binary files.

An .INP file is an OLE2 Compound Document with two streams:
DocumentInfo and InPage100. Text lives in InPage100 as 0x04-marker
byte pairs (the same encoding as InPage's text export), interleaved
with structure: '\\r' + 4 bytes marks a paragraph boundary, tabs and
printable ASCII are stored as bare bytes, and null-heavy regions
are layout/style structure, not text.

Verified against one real file (para1.inp, ~222k chars): output was
identical to InPage's own Unicode-text export except that the export
contained 4 stray junk bytes the binary does not — the direct read
was cleaner. The paragraph-boundary rule (\\r + exactly 4 structure
bytes) and the junk-region threshold below are derived from that one
file; other InPage versions may differ. Anything this parser is not
sure about ends up in the unmapped report, never silently guessed.
"""

import olefile

_UNDEFINED = {0x81, 0x8D, 0x8F, 0x90, 0x9D}


def _b2c(b: int) -> str:
    return chr(b) if b in _UNDEFINED else bytes([b]).decode("cp1252")


def is_inp(path_or_bytes) -> bool:
    """OLE2 magic check: D0 CF 11 E0."""
    if isinstance(path_or_bytes, (bytes, bytearray)):
        head = bytes(path_or_bytes[:8])
    else:
        with open(path_or_bytes, "rb") as f:
            head = f.read(8)
    return head[:4] == b"\xd0\xcf\x11\xe0"


def _find_long_run(data: bytes, pos: int, min_chars: int = 20) -> int:
    """Next offset >= pos where >= min_chars consecutive 0x04-pairs begin."""
    n = len(data)
    i = pos
    while i < n - 2 * min_chars:
        if data[i] == 0x04:
            j, c = i, 0
            while j < n - 1 and data[j] == 0x04:
                j += 2
                c += 1
                if c >= min_chars:
                    return i
            i = j + 1
        else:
            i += 1
    return -1


def extract_intermediate(path: str, junk_limit: int = 16,
                         min_block_chars: int = 10) -> list[str]:
    """Return text blocks in the intermediate (0x04-marker) form that
    herf.engine.convert() accepts. Block 0 is the main story; any
    further blocks are additional text regions found after structure
    gaps (text frames, footnotes, and similar)."""
    ole = olefile.OleFileIO(path)
    try:
        if not ole.exists("InPage100"):
            raise ValueError("No InPage100 stream — not a recognized InPage file.")
        data = ole.openstream("InPage100").read()
    finally:
        ole.close()

    n = len(data)
    blocks: list[str] = []
    buf: list[str] = []
    i = _find_long_run(data, 0)
    if i == -1:
        raise ValueError("No text found in this InPage file.")
    junk = 0
    while i < n:
        b = data[i]
        if b == 0x04 and i + 1 < n:
            buf.append("\u0004" + _b2c(data[i + 1]))
            i += 2
            junk = 0
        elif b == 0x0D:                     # paragraph mark + 4 structure bytes
            buf.append("\n")
            i += 5
            junk = 0
        elif b == 0x09:
            buf.append("\t")
            i += 1
            junk = 0
        elif 0x20 <= b <= 0x7E:             # bare ASCII is literal text
            buf.append(chr(b))
            i += 1
            junk = 0
        else:
            junk += 1
            i += 1
            if junk >= junk_limit:          # structure region: block over
                if len(buf) >= min_block_chars:
                    blocks.append("".join(buf))
                buf = []
                nxt = _find_long_run(data, i)
                if nxt == -1:
                    break
                i = nxt
                junk = 0
    if len(buf) >= min_block_chars:
        blocks.append("".join(buf))
    if not blocks:
        raise ValueError("No text blocks recovered from this InPage file.")
    return blocks
