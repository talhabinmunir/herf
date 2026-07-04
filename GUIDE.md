# Guide: converting your first file

This walks through the common path — converting an .inp file to a Word document — end to end. For install steps see [INSTRUCTIONS.md](INSTRUCTIONS.md); for a full reference of every control see [MANUAL.md](MANUAL.md).

## 1. Open Herf

Launch `Herf.exe` (or `python main.py` from source). You land on the **Convert** screen: a source pane on the left, a Unicode result pane on the right, and a settings/export panel on the far right.

## 2. Load your text

You have three options at the top of the screen:

- **Paste text** — paste InPage-exported text directly into the source box. Conversion runs automatically, a third of a second after you stop typing.
- **Open files** — pick one or more `.inp` or `.txt` files. Herf reads `.inp` files directly from the OLE2 container; no export from InPage needed.
- **Whole folder** — point Herf at a folder and it picks up every `.inp` and `.txt` file inside, in name order.

When you open files or a folder, each one appears as a card under **Files**; click any card to view its converted result in the right-hand pane.

## 3. Check the result

The right-hand stats card shows character count and how many unmapped byte codes were found. A clean conversion shows **Clean conversion**; if anything was flagged, it shows how many codes need review.

If any codes are unmapped, they're listed under **Unmapped codes** with a count and a snippet of surrounding text. Herf never guesses at these — for each one, you can type the correct character and click **Apply** to fix it everywhere in the current document and re-run the conversion.

## 4. Clean up (optional)

- **Fix spelling** — applies known rule-based fixes for InPage conversion artifacts (hamza joins, missing spaces, double spaces). A toast tells you exactly what changed and how many times.
- **Check Quran verses** — scans the result for Quranic quotations and compares them against the bundled Tanzil text. Matches at 75% similarity or above get a **Replace with Tanzil text** button; anything lower is flagged for manual review only. Nothing here is ever auto-replaced — you approve each verse individually.

## 5. Export

Once you're happy with the result, use the right-hand panel:

- **Save as Word (.docx)** — exports right-to-left, right-aligned, using the font selected in Settings.
- **Save as text (.txt)** — plain UTF-8 export.
- **Copy for Canva / Affinity** — copies the result to your clipboard for pasting into design tools.

## 6. Start over

**Clear** resets the source pane, result pane, file queue, and all reports so you can start on a new document.
