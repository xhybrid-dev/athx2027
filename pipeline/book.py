"""Shared facts about the ATHX 2027 book PDFs, for the cut-out pipeline.

Page geometry, the women's page mapping, and text positions from Poppler. Every
other pipeline script imports this; nothing here writes files.

Coordinates: PDF points (1/72 in) with the origin at the top left, as
`pdftotext -bbox` reports them, or pixels at DPI (300) where noted.
"""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DPI = 300
PX_PER_PT = DPI / 72

BOOKS = {
    "mens": ROOT / "assets/pdf/ATHX-2027-Mens.pdf",
    "womens": ROOT / "assets/pdf/ATHX-2027-Womens.pdf",
}
COVERS = {
    "mens": ROOT / "assets/pdf/ATHX-2027-Mens-COVER-white.pdf",
    "womens": ROOT / "assets/pdf/ATHX-2027-Womens-COVER-white.pdf",
}
PAGES_DIR = ROOT / "assets/pages"

# Interior pages are 513 x 738 pt: a 7 x 10 in trim (504 x 720 pt) plus 9 pt of
# bleed top and bottom and on the outside edge, which is the right of odd pages
# and the left of even pages (the text margins alternate to match).
TRIM_W, TRIM_H, BLEED = 504, 720, 9

# The women's edition adds Chapter 13, "Aligning the Block", as pages 43 to 45.
WOMENS_INSERT_AFTER, WOMENS_INSERT_PAGES = 42, 3

# Word box height = font size x this, for the fonts the book embeds. Inter boxes
# are 1.21 x size and Space Grotesk 1.28 x; using the larger gives a slightly
# low, so conservative, size estimate for legibility checks.
BOX_HEIGHT_PER_PT = 1.276


def book_page(edition: str, mens_page: int) -> int:
    """The page in `edition` that holds what the brief indexes as men's `mens_page`."""
    if edition == "mens" or mens_page <= WOMENS_INSERT_AFTER:
        return mens_page
    return mens_page + WOMENS_INSERT_PAGES


def trim_box_pt(page: int) -> tuple[float, float, float, float]:
    """The trimmed page, without bleed."""
    x0 = 0 if page % 2 else BLEED
    return (x0, BLEED, x0 + TRIM_W, BLEED + TRIM_H)


def cover_front_trim_pt(cover_width: float) -> tuple[float, float, float, float]:
    """The front cover panel of a wrap (back, spine, front), without bleed."""
    return (cover_width - BLEED - TRIM_W, BLEED, cover_width - BLEED, BLEED + TRIM_H)


def page_size_pt(pdf: Path) -> tuple[float, float]:
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True).stdout
    m = re.search(r"^Page size:\s+([\d.]+) x ([\d.]+) pts", info, re.M)
    return float(m.group(1)), float(m.group(2))


def page_png(edition: str, page: int) -> Path:
    return PAGES_DIR / f"{edition}-p{page:03d}.png"


def cover_png(edition: str) -> Path:
    return PAGES_DIR / f"{edition}-cover.png"


@dataclass
class Word:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float


@dataclass
class Row:
    """Words sharing a baseline, left to right: one line of text, or one table row."""

    words: list[Word]

    @property
    def text(self) -> str:
        return " ".join(w.text for w in self.words)

    @property
    def box(self) -> tuple[float, float, float, float]:
        return (
            min(w.x0 for w in self.words),
            min(w.y0 for w in self.words),
            max(w.x1 for w in self.words),
            max(w.y1 for w in self.words),
        )

    @property
    def size_pt(self) -> float:
        """Estimated font size of the row's largest word."""
        return max(w.y1 - w.y0 for w in self.words) / BOX_HEIGHT_PER_PT

    def cells(self, gap_pt: float = 6) -> list[list[Word]]:
        """Words split into cells wherever the space between them exceeds gap_pt."""
        cells: list[list[Word]] = [[self.words[0]]]
        for prev, w in zip(self.words, self.words[1:]):
            if w.x0 - prev.x1 > gap_pt:
                cells.append([w])
            else:
                cells[-1].append(w)
        return cells


_WORD = re.compile(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>')


def words(pdf: Path, page: int) -> list[Word]:
    out = subprocess.run(
        ["pdftotext", "-f", str(page), "-l", str(page), "-bbox", str(pdf), "-"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    unescape = lambda s: s.replace("&amp;", "&").replace("&apos;", "'").replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">")
    return [Word(unescape(t), float(a), float(b), float(c), float(d)) for a, b, c, d, t in _WORD.findall(out)]


def rows(pdf: Path, page: int, tolerance_pt: float = 2.0) -> list[Row]:
    """Words grouped into rows by baseline, top to bottom. Text in two columns at
    the same height (a table row, or a two-column panel) shares a row."""
    out: list[Row] = []
    for w in sorted(words(pdf, page), key=lambda w: (round(w.y1, 1), w.x0)):
        if out and abs(out[-1].words[-1].y1 - w.y1) <= tolerance_pt:
            out[-1].words.append(w)
        else:
            out.append(Row([w]))
    for r in out:
        r.words.sort(key=lambda w: w.x0)
    return out


def is_footer(row: Row) -> bool:
    return "EDITION | ATHX 2027" in row.text
