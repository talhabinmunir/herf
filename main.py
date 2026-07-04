"""Herf — InPage to Unicode converter for Windows.

Run:  python main.py
All processing is local. No file content leaves this machine.
"""

import json
import os
import sys
import webview

from herf.engine import convert_bytes, convert, decode_bytes

APP_DIR = os.path.dirname(os.path.abspath(__file__))


class Api:
    def __init__(self):
        self.user_mapping = {}
        self.last_text = ""

    # ---------- conversion ----------

    def convert_pasted(self, pasted, opts):
        """Pasted text arrives already unicode-decoded by the browser;
        re-encode via cp1252 to recover original bytes where possible."""
        try:
            raw = pasted.encode("cp1252", errors="replace")
        except Exception:
            raw = pasted.encode("utf-8")
        return self._run(raw, opts)

    def convert_file(self, path, opts):
        from herf.inp_reader import is_inp, extract_intermediate
        if path.lower().endswith(".inp") or is_inp(path):
            blocks = extract_intermediate(path)
            # main story first; any extra text regions appended, separated
            intermediate = "\n\n".join(blocks)
            text, report = convert(
                intermediate,
                user_mapping=self.user_mapping,
                latin_digits=opts.get("latinDigits", False),
                strip_kashida=opts.get("stripKashida", False),
            )
            self.last_text = text
            return {"text": text, "report": report, "chars": len(text),
                    "unmapped": sum(e["count"] for e in report),
                    "blocks": len(blocks), "source": "inp"}
        with open(path, "rb") as f:
            raw = f.read()
        return self._run(raw, opts)

    def _run(self, raw, opts):
        text, report = convert_bytes(
            raw,
            user_mapping=self.user_mapping,
            latin_digits=opts.get("latinDigits", False),
            strip_kashida=opts.get("stripKashida", False),
        )
        self.last_text = text
        return {"text": text, "report": report,
                "chars": len(text), "unmapped": sum(e["count"] for e in report)}


    # ---------- cleanup and Quran check ----------

    def fix_spelling(self, text):
        from herf.textfix import fix_spelling
        fixed, changes = fix_spelling(text)
        self.last_text = fixed
        return {"text": fixed, "changes": changes}

    def quran_scan(self, text):
        from herf.quran import QuranIndex, scan
        if not hasattr(self, "_qindex"):
            self._qindex = QuranIndex()
        matches = scan(text, self._qindex)
        return {"matches": matches, "count": len(matches)}

    def set_text(self, text):
        """UI pushes its authoritative text after client-side edits."""
        self.last_text = text
        return {"ok": True}

    # ---------- custom mappings ----------

    def add_mapping(self, code_hex, replacement):
        """code_hex like '0x04 0xE2'. Store and return updated mapping list."""
        parts = code_hex.split()
        b = int(parts[1], 16)
        undefined = {0x81, 0x8D, 0x8F, 0x90, 0x9D}
        ch = chr(b) if b in undefined else bytes([b]).decode("cp1252")
        self.user_mapping["\u0004" + ch] = replacement
        return {"ok": True, "count": len(self.user_mapping)}

    # ---------- files ----------

    def pick_files(self):
        w = webview.windows[0]
        result = w.create_file_dialog(
            webview.OPEN_DIALOG, allow_multiple=True,
            file_types=("InPage files (*.inp;*.INP;*.txt;*.TXT)",
                        "All files (*.*)"))
        return list(result) if result else []

    def pick_folder(self):
        w = webview.windows[0]
        result = w.create_file_dialog(webview.FOLDER_DIALOG)
        if not result:
            return []
        folder = result[0]
        out = []
        for name in sorted(os.listdir(folder)):
            if name.lower().endswith((".txt", ".inp")):
                out.append(os.path.join(folder, name))
        return out

    # ---------- export ----------

    def save_txt(self, text):
        w = webview.windows[0]
        path = w.create_file_dialog(
            webview.SAVE_DIALOG, save_filename="converted.txt")
        if not path:
            return {"ok": False}
        if isinstance(path, (list, tuple)):
            path = path[0]
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return {"ok": True, "path": path}

    def save_docx(self, text, font_name):
        try:
            from docx import Document
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            from docx.shared import Pt
            from docx.oxml.ns import qn
            from docx.oxml import OxmlElement
        except ImportError:
            return {"ok": False,
                    "error": "python-docx is not installed. Run: pip install python-docx"}

        w = webview.windows[0]
        path = w.create_file_dialog(
            webview.SAVE_DIALOG, save_filename="converted.docx")
        if not path:
            return {"ok": False}
        if isinstance(path, (list, tuple)):
            path = path[0]

        doc = Document()
        for para_text in text.split("\n"):
            if not para_text.strip():
                continue
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            # RTL paragraph direction
            pPr = p._p.get_or_add_pPr()
            bidi = OxmlElement("w:bidi")
            pPr.append(bidi)
            run = p.add_run(para_text)
            run.font.name = font_name
            run.font.size = Pt(14)
            rPr = run._r.get_or_add_rPr()
            rtl = OxmlElement("w:rtl")
            rPr.append(rtl)
            cs = OxmlElement("w:szCs")
            cs.set(qn("w:val"), "28")
            rPr.append(cs)
            rFonts = rPr.find(qn("w:rFonts"))
            if rFonts is None:
                rFonts = OxmlElement("w:rFonts")
                rPr.append(rFonts)
            rFonts.set(qn("w:cs"), font_name)
        doc.save(path)
        return {"ok": True, "path": path}

    def list_fonts(self):
        """Return installed font family names on Windows; fallback list otherwise."""
        try:
            import winreg
            fonts = set()
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts")
            i = 0
            while True:
                try:
                    name, _, _ = winreg.EnumValue(key, i)
                    fonts.add(name.split(" (")[0])
                    i += 1
                except OSError:
                    break
            return sorted(fonts)
        except Exception:
            return ["Jameel Noori Nastaleeq", "Urdu Typesetting",
                    "Noto Nastaliq Urdu", "Arial"]


def main():
    api = Api()
    webview.create_window(
        "Herf",
        os.path.join(APP_DIR, "herf", "ui", "index.html"),
        js_api=api,
        width=1280, height=820, min_size=(980, 640),
        background_color="#F7F1EA",
    )
    webview.start()


if __name__ == "__main__":
    main()
