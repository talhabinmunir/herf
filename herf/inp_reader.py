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

Character formatting (decoded against the same file, cross-checked
against InPage's own PDF export of it):

- The 4 bytes after each '\\r' are a little-endian uint32 equal to the
  byte length of the NEXT paragraph + 1 — a skip-ahead link, no style
  content (verified exact on all 570 paragraph pairs).
- Immediately after the story text (last '\\r' + 4 link bytes) comes a
  6-byte marker 00 00 FF FF FF FF, then a character-run style table:
  records of <run_bytes u32> <reclen u32> <0x0001 u16> <bloblen u32>
  <blob>, where reclen == 6 + bloblen and run_bytes counts text bytes
  exactly as stored (marker pair = 2, bare ASCII/tab = 1, '\\r' = 1,
  the 4 link bytes not counted).
- Each blob is a token stream of (opcode u16, value) pairs. Decoded
  opcodes: 0x7f00 value u32 = font size in 1/2000 pt (48000 = 24 pt;
  matches the PDF export exactly for 22/24/30 pt text); 0x7f08 value
  u16 = bold flag; 0x7f80 value u16 = font index (table not yet
  located). Opcodes 0x0080/0x7f06/0x7f8a (u32) and
  0x0040/0x7f02/0x0201/0x0202 (u16) are structurally understood
  (their value widths are proven by the fact that all 1300+ run blobs
  in the reference file parse cleanly) but their meanings are unknown
  and they are ignored. A blob containing an opcode outside this set
  is reported as style None — never guessed.
- The DocumentInfo stream in the reference file is all zeros; it holds
  no style table.
"""

import struct

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


# Style-blob opcodes and their value widths. Widths were proven by
# parsing every run blob in the reference file with them; meanings are
# only claimed for the opcodes actually used in _parse_style_blob.
_OP_U32 = {0x7f00, 0x7f06, 0x7f8a, 0x0080}
_OP_U16 = {0x7f80, 0x7f08, 0x7f02, 0x0201, 0x0202, 0x0040}


def _parse_style_blob(blob: bytes) -> dict | None:
    """Decode one run's attribute blob. Returns {'size': pt|None,
    'bold': bool} or None if any token is unrecognized."""
    size = None
    bold = False
    i = 0
    n = len(blob)
    while i + 2 <= n:
        op = struct.unpack_from("<H", blob, i)[0]
        i += 2
        if op in _OP_U32:
            if i + 4 > n:
                return None
            val = struct.unpack_from("<I", blob, i)[0]
            i += 4
        elif op in _OP_U16:
            if i + 2 > n:
                return None
            val = struct.unpack_from("<H", blob, i)[0]
            i += 2
        else:
            return None
        if op == 0x7f00:
            size = val / 2000
        elif op == 0x7f08:
            bold = bool(val)
    if i != n:
        return None
    return {"size": size, "bold": bold}


def _parse_style_runs(data: bytes, pos: int) -> list[tuple[int, dict | None]]:
    """Parse the character-run style table that follows the story text.
    pos points just past the last paragraph's CR + 4 link bytes.
    Returns [(run_byte_count, style_or_None), ...]; empty list if the
    table marker is not where this format version puts it."""
    marker = data.find(b"\xff\xff\xff\xff", pos, pos + 32)
    if marker == -1:
        return []
    pos = marker + 4
    runs: list[tuple[int, dict | None]] = []
    n = len(data)
    while pos + 14 <= n:
        count, reclen = struct.unpack_from("<II", data, pos)
        if count == 0 or count > 0x100000 or reclen < 8 or reclen > 512:
            break
        flag = struct.unpack_from("<H", data, pos + 8)[0]
        bloblen = struct.unpack_from("<I", data, pos + 10)[0]
        if flag != 1 or reclen != 6 + bloblen or pos + 14 + bloblen > n:
            break
        runs.append((count, _parse_style_blob(data[pos + 14:pos + 14 + bloblen])))
        pos += 8 + reclen
    return runs


def extract_document(path: str, junk_limit: int = 16,
                     min_block_chars: int = 10):
    """Extract text plus per-paragraph character styling.

    Returns (blocks, styles):
      blocks — list of intermediate-form text blocks, exactly as
        extract_intermediate() returns them (paragraphs joined by \\n).
      styles — parallel list: styles[b][p] belongs to paragraph p of
        blocks[b] (i.e. blocks[b].split("\\n")[p]) and is either None
        (no style recovered — never guessed) or
        {'size': pt|None, 'bold': bool, 'coverage': 0.0-1.0} where
        coverage is the fraction of the paragraph's bytes the dominant
        (size, bold) run combination actually spans.
    """
    ole = olefile.OleFileIO(path)
    try:
        if not ole.exists("InPage100"):
            raise ValueError("No InPage100 stream — not a recognized InPage file.")
        data = ole.openstream("InPage100").read()
    finally:
        ole.close()

    n = len(data)
    blocks: list[str] = []
    para_bytes: list[list[int]] = []    # per block, per paragraph: counted bytes
    buf: list[str] = []
    cur_paras: list[int] = []
    cur_bytes = 0                       # counted bytes of paragraph in progress
    text_end = -1                       # just past last CR + 4 link bytes
    i = _find_long_run(data, 0)
    if i == -1:
        raise ValueError("No text found in this InPage file.")
    junk = 0

    def close_block():
        nonlocal buf, cur_paras, cur_bytes
        if len(buf) >= min_block_chars:
            blocks.append("".join(buf))
            para_bytes.append(cur_paras + [cur_bytes])
        buf = []
        cur_paras = []
        cur_bytes = 0

    while i < n:
        b = data[i]
        if b == 0x04 and i + 1 < n:
            buf.append("" + _b2c(data[i + 1]))
            i += 2
            cur_bytes += 2
            junk = 0
        elif b == 0x0D:                     # paragraph mark + 4 link bytes
            buf.append("\n")
            cur_paras.append(cur_bytes + 1)  # +1: the CR itself is counted
            cur_bytes = 0
            i += 5
            text_end = i
            junk = 0
        elif b == 0x09:
            buf.append("\t")
            i += 1
            cur_bytes += 1
            junk = 0
        elif 0x20 <= b <= 0x7E:             # bare ASCII is literal text
            buf.append(chr(b))
            i += 1
            cur_bytes += 1
            junk = 0
        else:
            junk += 1
            i += 1
            cur_bytes += 1                  # stray bytes occupy run space
            if junk >= junk_limit:          # structure region: block over
                cur_bytes -= junk           # ...but a block gap does not
                close_block()
                nxt = _find_long_run(data, i)
                if nxt == -1:
                    break
                i = nxt
                junk = 0
    close_block()
    if not blocks:
        raise ValueError("No text blocks recovered from this InPage file.")

    runs = _parse_style_runs(data, text_end) if text_end != -1 else []

    # Assign each paragraph the dominant style among the runs covering
    # its byte span. Style stream position advances block by block in
    # file order; paragraphs past the end of the run table get None.
    styles: list[list[dict | None]] = []
    ri = 0                                  # current run index
    consumed = 0                            # bytes consumed of runs[ri]
    for bi in range(len(para_bytes)):
        block_styles: list[dict | None] = []
        for pb in para_bytes[bi]:
            agg: dict[tuple, int] = {}
            remaining = pb
            while remaining > 0 and ri < len(runs):
                avail = runs[ri][0] - consumed
                take = min(avail, remaining)
                st = runs[ri][1]
                if st is not None:
                    key = (st["size"], st["bold"])
                    agg[key] = agg.get(key, 0) + take
                consumed += take
                remaining -= take
                if consumed >= runs[ri][0]:
                    ri += 1
                    consumed = 0
            if agg and pb > 0:
                (size, bold), covered = max(agg.items(), key=lambda kv: kv[1])
                block_styles.append({"size": size, "bold": bold,
                                     "coverage": covered / pb})
            else:
                block_styles.append(None)
        styles.append(block_styles)
    return blocks, styles


def extract_intermediate(path: str, junk_limit: int = 16,
                         min_block_chars: int = 10) -> list[str]:
    """Return text blocks in the intermediate (0x04-marker) form that
    herf.engine.convert() accepts. Block 0 is the main story; any
    further blocks are additional text regions found after structure
    gaps (text frames, footnotes, and similar)."""
    blocks, _ = extract_document(path, junk_limit, min_block_chars)
    return blocks
