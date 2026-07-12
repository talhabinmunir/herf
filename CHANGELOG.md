# Changelog

All notable changes to Herf are documented here. Dates are in YYYY-MM-DD format.

## [1.1.0] - 2026-07-12

### Added

- Font size and bold recovery from `.inp` files. Herf now decodes the character-run style table that InPage stores after the story text (font size in 1/2000 pt units, bold flag), verified against InPage's own PDF export of the reference file: headings, verse quotations, and body text each keep their real point size in Word export instead of uniform 14 pt.
- Word export now preserves blank spacer paragraphs from the source (sized to match), so vertical spacing around headings survives conversion.
- Word export sets the complex-script size and bold (`szCs`, `bCs`) so Urdu text actually renders at the recovered size and weight.

### Known limits of style recovery

- Styling is applied per paragraph using the dominant run; inline changes within a paragraph (a bold word, an inline verse at a different size) are flattened to the paragraph's dominant style.
- Recovered styles apply to `.inp` input only — pasted text and `.txt` exports carry no style data and still export flat.
- If the text is edited after conversion in a way that changes the line count, styles no longer line up and the export falls back to flat formatting rather than guessing.
- Paragraph alignment and space-before/after attributes have not been decoded; export remains right-aligned throughout.

## [1.0.0] - 2026-07-04

Initial public release.

### Added

- Direct `.inp` file reading — pulls text straight from the InPage100 OLE2 stream, no InPage export step required.
- Paste-to-convert for InPage-exported text, plus `.txt` file and whole-folder batch conversion.
- Byte-pair mapping table (82 entries) for InPage-to-Unicode conversion.
- Unmapped-code reporting: any byte code without a mapping table entry is surfaced with its count and surrounding text context, with a way to supply the correct character and apply it across the document — never silently guessed.
- Export to UTF-8 `.txt`, right-to-left Word `.docx` (with selectable Urdu font), and clipboard copy for use in Canva or Affinity.
- Fix spelling: rule-based cleanup of known InPage conversion artifacts (hamza joins, missing spaces after noon-ghunna and taa marbuta, double spaces), with a per-rule change report.
- Check Quran verses: detects Quranic quotations by diacritic density and matches them against the bundled Tanzil Quran text (6,236 verses), with per-verse similarity scoring and manual approval required before any replacement.
- Settings for Latin vs. Urdu-Indic digits, kashida removal, and Word export font.
- Standalone Windows `.exe` build via PyInstaller.
