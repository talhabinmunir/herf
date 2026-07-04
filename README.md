# Herf

Converts InPage proprietary-encoded text to standard Unicode, locally on your Windows machine. Nothing is uploaded.

## What it does

- Open .inp files directly — no need to export from InPage first. Herf reads the OLE2 container and pulls the text out of the InPage100 stream. Tested against one real book file: the result matched InPage's own Unicode export exactly, minus 4 junk bytes that InPage's export had inserted and the direct read did not.
- Or paste InPage-exported text, or open .txt export files, or a whole folder (.inp and .txt both).
- Converts using a verified byte-pair mapping table (82 entries, sourced from the open-source ltrc/UmerCodez InPage converter projects, GPL).
- Any byte code NOT in the table is reported with its count and text context — never silently guessed. You can type the correct character for a flagged code and apply it across the whole document.
- Export: UTF-8 .txt, Word .docx (right-to-left, right-aligned, your chosen Urdu font), or copy to clipboard for Canva / Affinity.
- Fix spelling button: rule-based fixes for known InPage conversion artifacts, taken from the ltrc reference converter's own cleanup rules — standalone hamza before a letter becomes hamza-on-yeh (hu'i, ko'i, ja'e class), missing spaces after noon-ghunna and taa marbuta, double spaces. It reports exactly which rules changed how many places. This is artifact cleanup, not grammar correction: a real offline Urdu grammar checker is not something rules can do reliably, and Herf does not claim to.
- Check Quran verses button: detects Quranic quotations (by diacritic density) and matches them against the bundled Tanzil Quran text (6,236 verses, herf/data/quran.json, from the risan/quran-json distribution). Each match is shown side by side with surah:ayah and a similarity score. Replacement always needs your approval per verse; matches under 75% get no replace button at all and are marked for hand review. Scripture is never auto-corrected.
- Clear button: resets both panes, the queue, and all reports.
- Settings: Latin vs Urdu digits, kashida removal, Word export font.

## Getting started

See [INSTRUCTIONS.md](INSTRUCTIONS.md) to run from source or build a standalone .exe.

Already running Herf? See [GUIDE.md](GUIDE.md) for a walkthrough of converting your first file, or [MANUAL.md](MANUAL.md) for a full reference of every button and setting.

Version history: [CHANGELOG.md](CHANGELOG.md).

## Known limits

- Converts text content only — page layout, frames, and images are not recreated. The layout structures inside .inp files are undocumented, and Herf does not attempt to reverse them.
- The .inp parser's structure rules (paragraph mark = CR + 4 bytes, junk-region threshold) were derived from one real InPage 2016 file. Files from other InPage versions may behave differently; anything the parser is unsure of lands in the unmapped report rather than being guessed.
- Additional text regions in a document (text frames, footnotes) are appended after the main story, separated by a blank line, in stream order — not in visual page order.
- The UI loads the Poppins font from Google Fonts when online; offline it falls back to Segoe UI. Conversion itself works fully offline.

## License note

The character mapping table derives from GPL-licensed open-source projects (see herf/mapping.py). If you distribute Herf, the GPL applies to that component.
