"""Quran verse cross-checking.

Bundles the Tanzil-derived Uthmani Quran text (6,236 verses, standard
count, from the risan/quran-json distribution of the Tanzil text) and
matches Quranic quotations found in a converted document against it.

Design rule: this module SUGGESTS and never auto-replaces. Scripture
correction always requires the person's explicit approval per verse.
Matching works on a normalized form (diacritics stripped, letter
variants unified) so the Urdu-script style used in Pakistani books
(ہ ی ک) matches the Arabic-script Quran text (ه ي ك).
"""

import json
import os
import re
from difflib import SequenceMatcher

_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "data", "quran.json")

# Arabic diacritics, Quranic annotation marks, tatweel
_STRIP = re.compile(
    "[\u064B-\u065F\u0670\u06D6-\u06ED\u0640\u06E1\u0652\u0651"
    "\u0610-\u061A\u08D3-\u08FF\u0653\u0654\u0655]")

_UNIFY = str.maketrans({
    "ٱ": "ا", "أ": "ا", "إ": "ا", "آ": "ا", "ٲ": "ا", "ٳ": "ا",
    "ي": "ی", "ى": "ی", "ئ": "ی",
    "ه": "ہ", "ھ": "ہ", "ۂ": "ہ",
    "ة": "ۃ",
    "ك": "ک",
    "ؤ": "و",
    "ے": "ی",
})


def normalize(s: str) -> str:
    s = _STRIP.sub("", s)
    s = s.translate(_UNIFY)
    s = re.sub(r"[^\u0600-\u06FF ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


class QuranIndex:
    def __init__(self, path: str = _DATA):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self.verses = []          # (surah_no, surah_name, ayah_no, text, norm)
        self.trigrams = {}        # word-trigram -> set of verse indices
        for surah in data:
            for v in surah["verses"]:
                norm = normalize(v["text"])
                idx = len(self.verses)
                self.verses.append((surah["id"], surah["name"],
                                    v["id"], v["text"], norm))
                words = norm.split()
                for k in range(len(words) - 2):
                    tri = " ".join(words[k:k + 3])
                    self.trigrams.setdefault(tri, set()).add(idx)

    def best_match(self, segment_norm: str, min_votes: int = 2):
        """Return (verse_index, similarity) for the best-matching verse,
        or None. Candidate verses are found by trigram voting, then
        ranked by similarity of normalized texts."""
        words = segment_norm.split()
        votes = {}
        for k in range(len(words) - 2):
            tri = " ".join(words[k:k + 3])
            for idx in self.trigrams.get(tri, ()):
                votes[idx] = votes.get(idx, 0) + 1
        if not votes:
            return None
        candidates = sorted(votes.items(), key=lambda kv: -kv[1])[:8]
        if candidates[0][1] < min_votes:
            return None
        best, best_sim = None, 0.0
        for idx, _ in candidates:
            sim = SequenceMatcher(None, segment_norm,
                                  self.verses[idx][4]).ratio()
            if sim > best_sim:
                best, best_sim = idx, sim
        return (best, best_sim) if best is not None else None


_ARABIC_MARKS = re.compile("[\u064B-\u0652\u0670\u06E1]")


def looks_quranic(segment: str) -> bool:
    """Heuristic: Quranic quotations in these books carry full
    diacritics; ordinary Urdu prose carries almost none."""
    letters = len(re.findall(r"[\u0600-\u06FF]", segment))
    marks = len(_ARABIC_MARKS.findall(segment))
    return letters >= 12 and marks >= max(4, letters // 6)


def scan(text: str, index: QuranIndex, min_similarity: float = 0.55):
    """Find likely Quranic quotations and their best verified match.

    Returns a list of dicts:
      {found: str, surah_no, surah_name, ayah, verified: str, similarity}
    sorted by document order. Segments below min_similarity are skipped
    (better to miss than to suggest the wrong verse).
    """
    results = []
    seen = set()
    # candidate segments: sentence-ish chunks with heavy diacritics
    for m in re.finditer(r"[^\n۔]{18,500}", text):
        seg = m.group(0).strip()
        if not looks_quranic(seg):
            continue
        norm = normalize(seg)
        if len(norm.split()) < 3 or norm in seen:
            continue
        seen.add(norm)
        hit = index.best_match(norm)
        if not hit:
            continue
        idx, sim = hit
        if sim < min_similarity:
            continue
        s_no, s_name, a_no, verse_text, _ = index.verses[idx]
        results.append({
            "found": seg,
            "surah_no": s_no, "surah_name": s_name, "ayah": a_no,
            "verified": verse_text,
            "similarity": round(sim, 3),
            "position": m.start(),
        })
    results.sort(key=lambda r: r["position"])
    return results
