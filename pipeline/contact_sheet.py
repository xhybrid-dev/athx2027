"""Contact sheets for review.

Usage: python3 pipeline/contact_sheet.py cutouts          every cut-out, one scale, labelled
       python3 pipeline/contact_sheet.py overlays         each source page with its crop boxes
       python3 pipeline/contact_sheet.py frames VIDEO     one frame every 2 s (Gate 4 QA)

Writes to out/stills/. The cut-out sheet shows every cut-out at the same scale on
the near-black plate, as "paper on black", so relative sizes are honest; under
each one: where it comes from and the on-screen width its text needs to reach
20 px (from assets/cutouts/index.json).
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from book import ROOT, cover_png, page_png

STILLS = ROOT / "out/stills"
PLATE = (0x1C, 0x11, 0x17)
TEXT, MUTED = (255, 255, 255), (170, 165, 168)
ACCENT = (0xFB, 0xD8, 0x5B)
FONT = ROOT / "assets/fonts/Inter-Variable.ttf"
HEAD = ROOT / "assets/fonts/SpaceGrotesk-Variable.ttf"


def font(size: int, head: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(HEAD if head else FONT), size)


def paper_on_black(img: Image.Image) -> Image.Image:
    """The cut-out with the brief's soft shadow (0 12 32, black 35%), on the plate."""
    pad = 48
    canvas = Image.new("RGB", (img.width + 2 * pad, img.height + 2 * pad), PLATE)
    shadow = Image.new("L", canvas.size, 0)
    ImageDraw.Draw(shadow).rectangle((pad, pad + 12, pad + img.width, pad + 12 + img.height), fill=int(255 * 0.35))
    shadow = shadow.filter(ImageFilter.GaussianBlur(16))
    canvas.paste(Image.new("RGB", canvas.size, (0, 0, 0)), mask=shadow)
    canvas.paste(img, (pad, pad))
    return canvas


def cutouts_sheet() -> Path:
    index = json.loads((ROOT / "assets/cutouts/index.json").read_text())
    widths = index["layoutWidths"]
    scale, cols, cell_w, gap = 0.3, 3, 760, 24
    cards = []
    for c in index["cutouts"]:
        img = Image.open(ROOT / "assets" / c["file"]).convert("RGB")
        img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
        card = paper_on_black(img)
        lines = [
            (c["id"], TEXT, font(26, head=True)),
            (f"{c['edition']} p{c['page']} · {c['width']} x {c['height']} px · {c['use']}", MUTED, font(20)),
        ]
        leg = c.get("legibility")
        if leg:
            fits = [k for k, w in widths.items() if w >= leg["widthFor20pxMain"]]
            lines.append(
                (
                    f"main {leg['mainPt']} pt: 20 px at {leg['widthFor20pxMain']} px wide"
                    f" ({', '.join(fits) if fits else 'no layout width'})",
                    TEXT,
                    font(20),
                )
            )
            lines.append(
                (f"smallest {leg['smallestPt']} pt: 20 px at {leg['widthFor20pxSmallest']} px wide", MUTED, font(20))
            )
        elif "cover" in c["id"]:
            lines.append(("cover, full-bleed design", MUTED, font(20)))
        else:
            lines.append(("background texture at 25%: legibility not required", MUTED, font(20)))
        cards.append((card, lines))

    label_h = 140
    rows = [cards[i : i + cols] for i in range(0, len(cards), cols)]
    row_h = [max(card.height for card, _ in r) + label_h for r in rows]
    title_h = 120
    sheet = Image.new("RGB", (cols * cell_w + (cols + 1) * gap, title_h + sum(row_h) + gap), PLATE)
    d = ImageDraw.Draw(sheet)
    d.text((gap + 24, 36), "GATE 1 CUT-OUTS", fill=TEXT, font=font(44, head=True))
    d.text(
        (gap + 430, 52),
        f"All at {int(scale * 100)}% of the 300 dpi crop · 20 px widths: 16:9 full {widths['16:9 full']}, half {widths['16:9 half']}, 9:16 safe {widths['9:16 safe']}",
        fill=MUTED,
        font=font(22),
    )
    d.rectangle((gap + 24, 100, gap + 24 + 120, 104), fill=ACCENT)
    y = title_h
    for r, h in zip(rows, row_h):
        for i, (card, lines) in enumerate(r):
            x = gap + i * (cell_w + gap)
            sheet.paste(card, (x + (cell_w - card.width) // 2 if card.width < cell_w else x, y))
            ty = y + h - label_h + 8
            for text, colour, f in lines:
                d.text((x + 24, ty), text, fill=colour, font=f)
                ty += f.size + 10
        y += h
    out = STILLS / "gate1-cutouts.png"
    sheet.save(out, optimize=True)
    return out


def overlays_sheet() -> Path:
    crops = json.loads((ROOT / "pipeline/crops.json").read_text())["crops"]
    pages: dict[tuple, list] = {}
    for c in crops:
        key = (c["edition"], "cover" if c["mode"] == "cover-front" else c["page"])
        pages.setdefault(key, []).append(c)
    scale, cols, gap = 0.2, 6, 24
    thumbs = []
    for (ed, page), cs in pages.items():
        src = cover_png(ed) if page == "cover" else page_png(ed, page)
        img = Image.open(src).convert("RGB")
        d = ImageDraw.Draw(img)
        for c in cs:
            d.rectangle(c["box"], outline=ACCENT, width=10)
            d.text((c["box"][0] + 14, c["box"][1] + 10), c["id"], fill=(200, 60, 0), font=font(44))
        img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
        thumbs.append((img, f"{ed} {'cover wrap' if page == 'cover' else f'p{page}'}"))
    cell_w = max(t.width for t, _ in thumbs if t.width < 600)
    rows = []
    row: list = []
    used = 0
    for t in thumbs:
        span = 2 if t[0].width > cell_w else 1
        if used + span > cols:
            rows.append(row)
            row, used = [], 0
        row.append((t, span))
        used += span
    rows.append(row)
    row_h = [max(t[0].height for t, _ in r) + 50 for r in rows]
    sheet = Image.new("RGB", (cols * (cell_w + gap) + gap, sum(row_h) + 100), PLATE)
    d = ImageDraw.Draw(sheet)
    d.text((gap, 30), "GATE 1 CROP BOXES ON THEIR PAGES", fill=TEXT, font=font(36, head=True))
    y = 100
    for r, h in zip(rows, row_h):
        x = gap
        for (img, label), span in r:
            sheet.paste(img, (x, y))
            d.text((x, y + img.height + 10), label, fill=MUTED, font=font(20))
            x += span * (cell_w + gap)
        y += h
    out = STILLS / "gate1-crop-boxes.png"
    sheet.save(out, optimize=True)
    return out


def frames_sheet(video: Path) -> Path:
    """One frame every 2 s, 6 across, timecode under each (scope 8, Gate 4)."""
    with tempfile.TemporaryDirectory() as t:
        subprocess.run(
            ["ffmpeg", "-v", "error", "-i", str(video), "-vf", "fps=1/2,scale=480:-2", f"{t}/f%04d.png"],
            check=True,
        )
        frames = sorted(Path(t).glob("f*.png"))
        if not frames:
            sys.exit("no frames extracted")
        first = Image.open(frames[0])
        cols, gap, label = 6, 12, 30
        rows = (len(frames) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * (first.width + gap) + gap, rows * (first.height + label + gap) + gap), PLATE)
        d = ImageDraw.Draw(sheet)
        for i, f in enumerate(frames):
            x = gap + (i % cols) * (first.width + gap)
            y = gap + (i // cols) * (first.height + label + gap)
            sheet.paste(Image.open(f), (x, y))
            s = i * 2
            d.text((x, y + first.height + 4), f"{s // 60}:{s % 60:02d}", fill=MUTED, font=font(18))
    out = STILLS / f"frames-{video.stem}.png"
    sheet.save(out, optimize=True)
    return out


def main() -> None:
    STILLS.mkdir(parents=True, exist_ok=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else "cutouts"
    if mode == "cutouts":
        out = cutouts_sheet()
    elif mode == "overlays":
        out = overlays_sheet()
    elif mode == "frames" and len(sys.argv) > 2:
        out = frames_sheet(Path(sys.argv[2]))
    else:
        sys.exit(__doc__)
    print(f"  wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
