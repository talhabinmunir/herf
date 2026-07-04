# Manual

Full reference of every screen, button, and setting in Herf. For a task-oriented walkthrough, see [GUIDE.md](GUIDE.md).

## Sidebar

| Control | Behavior |
|---|---|
| **Convert** (top icon) | The only screen in the app; always active. |
| **About** (bottom icon) | Shows a toast: "Herf · local InPage to Unicode conversion · nothing is uploaded." |

## Input mode pills

| Control | Behavior |
|---|---|
| **✦ Paste text** | Focuses the source text box for pasting. Conversion is triggered automatically 350ms after you stop typing. |
| **🗂 Open files** | Opens a file picker filtered to InPage files (`*.inp`, `*.txt`) plus an "All files" option. Multiple selection is allowed. Each selected file is converted and added to the **Files** queue below. |
| **📁 Whole folder** | Opens a folder picker. Every `.txt` and `.inp` file in that folder (not subfolders), sorted by name, is queued and converted. If none are found, a toast says so. |

## Source pane

Plain text box. Paste raw InPage-exported bytes here (re-interpreted from cp1252 to recover the original encoding). Disabled while a file/folder queue is active — clear the queue or start typing to switch back to paste mode.

## Unicode result pane

Shows the converted text, right-to-left, in your selected Urdu font. Long results are truncated to the first 20,000 characters for display (the full text is still used for export). The badge above it shows the character count of the current result.

Buttons under the result pane:

| Button | Behavior |
|---|---|
| **Fix spelling** | Runs rule-based artifact cleanup (see [README.md](README.md#what-it-does) for the exact rules). Disabled until a result exists. Reports total fixes and a breakdown by rule via toast. |
| **Check Quran verses** | Scans the current result for Quranic quotations and matches them against the bundled Tanzil text. Populates the **Quran verse check** card in the side panel. Disabled until a result exists. |
| **Clear** | Resets the source box, result pane, file queue, unmapped-codes report, and Quran check card. Always enabled. |

## Files queue

Appears once you open files or a folder. Each file is shown as a card with:

- A badge: **✓ clean** if every byte code mapped, or **⚠ N unmapped** if not.
- The file name and character count.

Click any card to load that file's result into the Unicode result pane and all the side-panel stats/reports.

## Side panel

### Stats card

- **Characters** — length of the currently displayed result.
- **Unmapped** — count of byte codes in the current result with no mapping table entry.
- Status chip: **Ready** (nothing converted yet), **Clean conversion** (no unmapped codes), or **N codes need review** (unmapped codes present, chip turns pink).

### Unmapped codes card

Lists every byte code encountered that isn't in Herf's mapping table, each with:

- The byte code (e.g. `0x04 0xE2`) and how many times it occurred.
- A snippet of surrounding text for context, so you can judge the correct character from meaning.
- A text field and **Apply** button — type the correct replacement character(s) and click Apply to save that mapping and immediately re-convert the current document (or file queue) with it applied.

If nothing is flagged, the card shows: "Nothing flagged. Codes the mapping table does not know will be listed here — never replaced with a guess."

Mappings you apply are session-only (kept in memory while Herf is running) and apply to every file converted afterward in that session, not just the one you were viewing.

### Quran verse check card

Hidden until you run **Check Quran verses** at least once. For each detected passage:

- Similarity percentage (rounded), and the surah number, surah name, and ayah number of the closest Tanzil match.
- The passage **In document** and the corresponding **Tanzil text**, shown side by side in Arabic script.
- If similarity is 75% or higher: a **Replace with Tanzil text** button. Clicking it substitutes the matched passage in place, in the live result — but only if the passage still exists unchanged in the text (if you've edited it since scanning, you're told to re-run the check). Once replaced, the button becomes disabled and reads "Replaced."
- If similarity is below 75%: no replace button. A note reads "Partial or mixed quote — review by hand." You must fix these manually if needed.

If no Quranic passages are detected at all, the card shows "No Quranic quotations detected."

### Settings card

| Setting | Behavior |
|---|---|
| **Word font** | Dropdown of fonts installed on your Windows machine (queried from the registry at startup), with Jameel Noori Nastaleeq, Noto Nastaliq Urdu, and Urdu Typesetting preferred/prioritized if present. Used only for the .docx export. |
| **Latin digits (0-9)** | Checkbox. When checked, numerals in the converted output use 0-9 instead of Urdu-Indic digits (٠-٩). Toggling immediately re-converts the current text or file queue. |
| **Remove kashida** | Checkbox. When checked, kashida (tatweel, the Arabic justification-stretch character) is stripped from the output. Toggling immediately re-converts. |

### Export buttons

| Button | Behavior |
|---|---|
| **Save as Word (.docx)** | Opens a save dialog (default name `converted.docx`). Exports each non-empty line as a right-to-left, right-aligned paragraph in the font chosen in Settings, at 14pt. Requires `python-docx`; if missing, shows an error toast instead of failing silently. |
| **Save as text (.txt)** | Opens a save dialog (default name `converted.txt`). Exports the full result as UTF-8 plain text. |
| **Copy for Canva / Affinity** | Copies the full result text to the system clipboard, for pasting directly into design tools that don't accept file imports. |

All three export buttons (plus Fix spelling and Check Quran verses) are disabled until at least one conversion has produced a result.

## Toast notifications

A dark pill notification appears at the bottom of the screen for transient feedback — save confirmations, error messages, rule-fix summaries, and the About screen's description. Each toast auto-dismisses after ~2.6 seconds.
