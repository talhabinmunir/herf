# Changelog

All notable changes to Herf are documented here. Dates are in YYYY-MM-DD format.

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
