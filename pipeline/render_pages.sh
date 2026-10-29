#!/usr/bin/env bash
# Render every page that pipeline/crops.json uses, at 300 dpi, from the colour
# PDFs: assets/pages/<edition>-p<NNN>.png, plus <edition>-cover.png for the
# cover wraps. Pages already rendered from an unchanged PDF are skipped.
#
# Usage: pipeline/render_pages.sh

set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p assets/pages

python3 - <<'EOF' | while read -r edition page pdf out; do
import json, sys
sys.path.insert(0, "pipeline")
from book import BOOKS, COVERS, book_page, page_png, cover_png
seen = set()
for c in json.load(open("pipeline/crops.json"))["crops"]:
    ed = c["edition"]
    if c["mode"] == "cover-front":
        job = (ed, 1, COVERS[ed], cover_png(ed))
    else:
        p = book_page(ed, c["bookPage"])
        job = (ed, p, BOOKS[ed], page_png(ed, p))
    if job[3] not in seen:
        seen.add(job[3])
        print(*job)
EOF
	if [[ -f "$out" && "$out" -nt "$pdf" ]]; then
		echo "  kept     $(basename "$out")"
		continue
	fi
	pdftoppm -r 300 -f "$page" -l "$page" -png -singlefile "$pdf" "${out%.png}"
	echo "  rendered $(basename "$out")"
done
