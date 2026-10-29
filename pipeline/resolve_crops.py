"""Resolve every crop in pipeline/crops.json to a pixel box on its 300 dpi page.

Usage: python3 pipeline/resolve_crops.py            resolve all, rewrite crops.json
       python3 pipeline/resolve_crops.py --grid ID  also draw ID's box on a
                                                    coordinate grid, for checking by eye

Run pipeline/render_pages.sh first. For an element crop:

1. Find the anchor rows with pdftotext -bbox: the first row starting with
   anchor.first, then the nth row after it starting with anchor.last.
2. Take the box around those rows and everything between them.
3. Snap outwards on the render until GAP px of clear paper on every side, so the
   element's own fills, rules and edge bars are inside the box however far they
   reach past its text.
4. Add the 8 px margin (scope 6.1) and check that margin is clear paper. Ink in
   the margin means a neighbouring element sits too close, or something is
   clipped; the script fails rather than guess.

The other modes take their box from page geometry (see crops.json "about").
"""

import argparse
import json
import math
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from book import (
    BOOKS,
    COVERS,
    PX_PER_PT,
    ROOT,
    Row,
    book_page,
    cover_front_trim_pt,
    cover_png,
    is_footer,
    page_png,
    page_size_pt,
    rows,
    trim_box_pt,
)

CROPS = ROOT / "pipeline/crops.json"
MARGIN = 8  # px of clear paper kept around an element (scope 6.1)
INK = 250  # a pixel darker than this, in luminance, is ink: catches the palest table fill
GAP = 28  # px of clear paper that ends an element: about 6.7 pt
DAY_PAD_PT = 12  # day pages: padding either side of the text column
DAY_TOP_PT = 16  # day pages: space kept above the week label, inside the black band


def px_box(pt_box, inward=False):
    """Points to pixels. Outward rounding by default; inward for trim boxes, so
    no bleed survives."""
    x0, y0, x1, y1 = (v * PX_PER_PT for v in pt_box)
    if inward:
        return math.ceil(x0), math.ceil(y0), math.floor(x1), math.floor(y1)
    return math.floor(x0), math.floor(y0), math.ceil(x1), math.ceil(y1)


def has_ink(img, box) -> bool:
    x0, y0, x1, y1 = box
    if x1 <= x0 or y1 <= y0:
        return False
    return img.crop(box).getextrema()[0] < INK


def snap(img, box, gap):
    """Grow box until every side has `gap` px of clear paper beyond its last ink."""
    w, h = img.size
    x0, y0, x1, y1 = box
    while True:
        before = (x0, y0, x1, y1)
        # Each side: walk outwards one px strip at a time, remember the last inked
        # strip, stop after `gap` clear ones.
        last, clear, y = y0, 0, y0 - 1
        while y >= 0 and clear < gap:
            if has_ink(img, (x0, y, x1, y + 1)):
                last, clear = y, 0
            else:
                clear += 1
            y -= 1
        y0 = last
        last, clear, y = y1, 0, y1
        while y < h and clear < gap:
            if has_ink(img, (x0, y, x1, y + 1)):
                last, clear = y + 1, 0
            else:
                clear += 1
            y += 1
        y1 = last
        last, clear, x = x0, 0, x0 - 1
        while x >= 0 and clear < gap:
            if has_ink(img, (x, y0, x + 1, y1)):
                last, clear = x, 0
            else:
                clear += 1
            x -= 1
        x0 = last
        last, clear, x = x1, 0, x1
        while x < w and clear < gap:
            if has_ink(img, (x, y0, x + 1, y1)):
                last, clear = x + 1, 0
            else:
                clear += 1
            x += 1
        x1 = last
        if (x0, y0, x1, y1) == before:
            return before


def inked_margin(img, box) -> list[str]:
    """Sides of the margin ring around an element that are not clear paper."""
    x0, y0, x1, y1 = box
    m = MARGIN
    ring = {
        "top": (x0, y0, x1, y0 + m),
        "bottom": (x0, y1 - m, x1, y1),
        "left": (x0, y0, x0 + m, y1),
        "right": (x1 - m, y0, x1, y1),
    }
    return [side for side, b in ring.items() if has_ink(img, b)]


def find(page_rows: list[Row], text: str, after: float = -1, nth: int = 1) -> Row:
    seen = 0
    for r in page_rows:
        if r.box[1] > after and r.text.startswith(text):
            seen += 1
            if seen == nth:
                return r
    raise LookupError(f'no row starting "{text}"' + (f" (occurrence {nth})" if nth > 1 else ""))


def resolve(crop: dict) -> tuple[dict, list[str]]:
    """Returns the resolved fields and a list of problems."""
    ed, mode = crop["edition"], crop["mode"]
    problems: list[str] = []
    if mode == "cover-front":
        pdf, page = COVERS[ed], 1
        img = Image.open(cover_png(ed)).convert("L")
        box = px_box(cover_front_trim_pt(page_size_pt(pdf)[0]), inward=True)
        return {"pdf": str(pdf.relative_to(ROOT)), "page": page, "box": list(box)}, problems

    pdf = BOOKS[ed]
    page = book_page(ed, crop["bookPage"])
    img = Image.open(page_png(ed, page)).convert("L")
    trim = px_box(trim_box_pt(page), inward=True)
    gap = crop.get("gap", GAP)
    out = {"pdf": str(pdf.relative_to(ROOT)), "page": page}

    if mode == "page":
        out["box"] = list(trim)
        return out, problems

    page_rows = [r for r in rows(pdf, page) if not is_footer(r)]
    anchor = crop["anchor"]
    if mode == "day-page":
        # The page's text column, padded, from just above the week label down to
        # the last anchor. The black header band is cut at the column's edges.
        first = find(page_rows, anchor["first"])
        last = find(page_rows, anchor["last"], after=first.box[1], nth=anchor.get("lastNth", 1))
        col = px_box(
            (
                min(r.box[0] for r in page_rows) - DAY_PAD_PT,
                first.box[1] - DAY_TOP_PT,
                max(r.box[2] for r in page_rows) + DAY_PAD_PT,
                last.box[3],
            )
        )
        ink = snap(img, px_box(last.box), gap)
        out["box"] = [max(col[0], trim[0]), max(col[1], trim[1]), min(col[2], trim[2]), min(ink[3] + MARGIN, trim[3])]
        return out, problems

    first = find(page_rows, anchor["first"])
    last = find(page_rows, anchor["last"], after=first.box[1] - 0.1, nth=anchor.get("lastNth", 1))
    inside = [r for r in page_rows if r.box[1] >= first.box[1] - 0.1 and r.box[3] <= last.box[3] + 0.1]
    text_box = (
        min(r.box[0] for r in inside),
        first.box[1],
        max(r.box[2] for r in inside),
        last.box[3],
    )
    ink = snap(img, px_box(text_box), gap)
    box = (ink[0] - MARGIN, ink[1] - MARGIN, ink[2] + MARGIN, ink[3] + MARGIN)
    w, h = img.size
    if box[0] < 0 or box[1] < 0 or box[2] > w or box[3] > h:
        problems.append("box runs off the page")
    if (sides := inked_margin(img, box)):
        problems.append("ink in the margin: " + ", ".join(sides))
    out["box"] = list(box)
    return out, problems


def draw_grid(crop: dict) -> Path:
    """The crop's page with a 100 px coordinate grid and the box in yellow, at half size."""
    ed = crop["edition"]
    src = cover_png(ed) if crop["mode"] == "cover-front" else page_png(ed, crop["page"])
    img = Image.open(src).convert("RGB")
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(str(ROOT / "assets/fonts/Inter-Variable.ttf"), 22)
    w, h = img.size
    for x in range(0, w, 100):
        d.line([(x, 0), (x, h)], fill=(0, 160, 255) if x % 500 else (0, 90, 200), width=1)
        if x % 500 == 0:
            d.text((x + 4, 4), str(x), fill=(0, 90, 200), font=font)
    for y in range(0, h, 100):
        d.line([(0, y), (w, y)], fill=(0, 160, 255) if y % 500 else (0, 90, 200), width=1)
        if y % 500 == 0:
            d.text((4, y + 4), str(y), fill=(0, 90, 200), font=font)
    d.rectangle(crop["box"], outline=(251, 216, 91), width=4)
    out = ROOT / f"out/stills/grid-{crop['id']}.png"
    img.resize((w // 2, h // 2), Image.LANCZOS).save(out)
    return out


def write(doc: dict) -> None:
    text = json.dumps(doc, indent=2, ensure_ascii=False)
    # Keep lists of numbers on one line: "box": [x0, y0, x1, y1].
    text = re.sub(
        r"\[\s*(-?[\d.]+(?:,\s*-?[\d.]+)*)\s*\]",
        lambda m: "[" + ", ".join(v.strip() for v in m.group(1).split(",")) + "]",
        text,
    )
    CROPS.write_text(text + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", metavar="ID", help="also draw this crop's box on a coordinate grid")
    args = ap.parse_args()

    doc = json.loads(CROPS.read_text())
    failed = 0
    for crop in doc["crops"]:
        try:
            resolved, problems = resolve(crop)
        except LookupError as e:
            print(f"  FAIL  {crop['id']}: {e}")
            failed += 1
            continue
        crop.update(resolved)
        x0, y0, x1, y1 = crop["box"]
        status = "ok  " if not problems else "FAIL"
        failed += bool(problems)
        print(f"  {status}  {crop['id']:<24} {crop['edition']:<6} p{crop['page']:<4} {x1 - x0:>5} x {y1 - y0:<5} {'; '.join(problems)}")
    write(doc)
    if args.grid:
        crop = next(c for c in doc["crops"] if c["id"] == args.grid)
        print(f"  grid  {draw_grid(crop).relative_to(ROOT)}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
