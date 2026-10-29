"""Cut every resolved crop in pipeline/crops.json out of its 300 dpi page.

Usage: python3 pipeline/crop_cutouts.py

Writes assets/cutouts/<id>.png at native resolution (never rescaled, scope 6.1)
and assets/cutouts/index.json, which components read at Gate 2:

- size of each cut-out in px;
- rows: every line of text inside it, as px boxes relative to the cut-out, with
  its text and cells, for row-by-row builds, highlight bands and underlines;
- legibility: the smallest and the main text size (pt, estimated from the word
  boxes) and the on-screen width the cut-out needs for each to reach the scope's
  20 px minimum.

Fails if an element crop's 8 px margin is not clear paper (re-checked here in
case a box was edited by hand).
"""

import json
import sys
from collections import Counter

from PIL import Image

from book import BOOKS, COVERS, PX_PER_PT, ROOT, cover_png, is_footer, page_png, rows
from resolve_crops import CROPS, MARGIN, inked_margin

OUT = ROOT / "assets/cutouts"
MIN_TEXT_PX = 20  # scope 4.2: nothing on screen smaller than 20 px at 1080p
# Widths a cut-out can occupy (scope 4.3): the 16:9 grid at full and half width,
# and the 9:16 safe zone.
LAYOUT_WIDTHS = {"16:9 full": 1728, "16:9 half": 852, "9:16 safe": 900}


def width_for(size_pt: float, width_px: int) -> int:
    """On-screen width at which text of size_pt reaches MIN_TEXT_PX."""
    return round(width_px * MIN_TEXT_PX / (size_pt * PX_PER_PT))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    doc = json.loads(CROPS.read_text())
    index, failed = [], 0
    for crop in doc["crops"]:
        ed, mode = crop["edition"], crop["mode"]
        cover = mode == "cover-front"
        src = cover_png(ed) if cover else page_png(ed, crop["page"])
        page = Image.open(src).convert("RGB")
        x0, y0, x1, y1 = crop["box"]
        if mode == "element" and (sides := inked_margin(page.convert("L"), crop["box"])):
            print(f"  FAIL  {crop['id']}: ink in the margin ({', '.join(sides)})")
            failed += 1
            continue
        cut = page.crop((x0, y0, x1, y1))
        cut.save(OUT / f"{crop['id']}.png", optimize=True)

        pdf = COVERS[ed] if cover else BOOKS[ed]
        inside = []
        for r in rows(pdf, crop["page"]):
            bx0, by0, bx1, by1 = (v * PX_PER_PT for v in r.box)
            if is_footer(r) or by0 < y0 or by1 > y1 or bx0 < x0 or bx1 > x1:
                continue
            inside.append(
                {
                    "text": r.text,
                    "box": [round(bx0 - x0), round(by0 - y0), round(bx1 - x0), round(by1 - y0)],
                    "sizePt": round(r.size_pt, 1),
                    "cells": [
                        {
                            "text": " ".join(w.text for w in cell),
                            "x0": round(cell[0].x0 * PX_PER_PT - x0),
                            "x1": round(cell[-1].x1 * PX_PER_PT - x0),
                        }
                        for cell in r.cells()
                    ],
                }
            )

        entry = {
            "id": crop["id"],
            "file": f"cutouts/{crop['id']}.png",
            "use": crop["use"],
            "edition": ed,
            "page": crop["page"],
            "width": cut.width,
            "height": cut.height,
            "rows": inside,
        }
        if inside and not cover and not crop.get("texture"):
            sizes = [r["sizePt"] for r in inside]
            # The main text size: the one carrying the most words.
            weight = Counter()
            for r in inside:
                weight[r["sizePt"]] += len(r["text"].split())
            body = weight.most_common(1)[0][0]
            smallest = min(sizes)
            entry["legibility"] = {
                "smallestPt": smallest,
                "mainPt": body,
                "widthFor20pxMain": width_for(body, cut.width),
                "widthFor20pxSmallest": width_for(smallest, cut.width),
            }
        index.append(entry)
        leg = entry.get("legibility")
        note = (
            f"main {leg['mainPt']}pt needs {leg['widthFor20pxMain']}px, smallest {leg['smallestPt']}pt needs {leg['widthFor20pxSmallest']}px"
            if leg
            else ""
        )
        print(f"  ok    {crop['id']:<24} {cut.width:>5} x {cut.height:<5} {len(inside):>3} rows  {note}")

    (OUT / "index.json").write_text(json.dumps({"layoutWidths": LAYOUT_WIDTHS, "cutouts": index}, indent=1) + "\n")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
