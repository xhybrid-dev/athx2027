# Edit log: HYROX or ATHX?

Decisions, component names and open questions, newest gate first. The brief is
`VIDEO-BRIEF-HYROX-ATHX.md`, the scope is `VIDEO-PRODUCTION-SCOPE.md`, and
`PRODUCTION-PLAN.md` holds the agreed fixes and the recording script.

## Working commands

```bash
pipeline/bootstrap.sh          # fresh container: restore tools, deps, fonts; 1 s smoke render
pipeline/bootstrap.sh --check  # report only
npm run check                  # typecheck, facts and timings checks, VO fit report
pipeline/check_pdfs.sh         # page counts and RGB check of assets/pdf
npm run cutouts                # pages, crops, cut-outs and contact sheets from the PDFs
pipeline/clean_vo.sh           # assets/audio/vo/*.wav -> vo-clean/, -16 LUFS
pipeline/measure_loudness.sh   # EBU R128 report; --target -14 -1 for the final mix
npm run studio                 # Remotion Studio (needs a port forward to view)
npm run render:test            # the Gate 0 one-second render
npm run still:test:portrait    # the same card at 1080 x 1920
```

## Gate status

| Gate | State |
|---|---|
| 0. Setup | Approved 2026-10-29 |
| 1. Assets | **Delivered 2026-10-29 on branch `gate-1`, awaiting review** (Q10 to Q13) |
| 2. Design | Next: components, stills in both aspects, 10 s motion test |

---

## Gate 1: Assets (2026-10-29, branch `gate-1`)

### Delivered

- **Page renders.** 16 at 300 dpi from the colour PDFs: 14 interior pages and 2
  cover wraps, in `assets/pages/` (`pipeline/render_pages.sh`).
- **18 cut-outs** in `assets/cutouts/`, with `index.json`. Every cut-out in the
  brief's index that a storyboard uses, for both videos, plus the SkillCard sources.
  - Contact sheet: `out/stills/gate1-cutouts.png`.
  - Each crop box drawn on its page: `out/stills/gate1-crop-boxes.png`.
  - The pages, cut-outs and sheets are not in git (they come from paid PDFs);
    `npm run cutouts` regenerates all of them in about 30 s, and
    `pipeline/bootstrap.sh` does so on a fresh container when the PDFs are present.
- **Footage inventory.** None: this is an animation-only video.
- **Voiceover chain.** `pipeline/clean_vo.sh` (scope 6.3 chain, de-esser
  `i=0.4:m=0.5:f=0.5:s=o` per correction 10, two-pass loudnorm to -16 LUFS / -1.5
  dBTP, 48 kHz 24-bit mono) and `pipeline/measure_loudness.sh` (EBU R128 report;
  `--target -14 -1` fails out-of-spec files for Gate 4). Tested on a synthetic 12 s
  read only: -40.0 LUFS in, -16.0 LUFS / -4.0 dBTP out. No cleaned samples of
  Jon's voice yet; see the gaps list.
- `pipeline/contact_sheet.py frames VIDEO` (one frame every 2 s) is ready for Gate 4.

### The cut-outs

"20 px at" is the on-screen width at which the cut-out's main text, and then its
smallest text, reaches the scope's 20 px minimum. Layout widths: 16:9 full grid
1728 px, half 852 px; 9:16 safe zone 900 px.

| Cut-out | Used in | Source | Native px | Main text 20 px at | Smallest text 20 px at |
|---|---|---|---|---|---|
| `s04-scoring-table` | main 4c | mens p9 | 1696 x 219 | 958 px (8.5 pt) | 1147 px (7.1 pt) |
| `s06-strength-windows` | main 6a SkillCard 1 | mens p5 | 1696 x 345 | 958 px (8.5 pt) | 1147 px (7.1 pt) |
| `s06-worked-example` | main 6b | mens p12 | 1696 x 521 | 936 px (8.7 pt) | 1100 px (7.4 pt) |
| `s06-split-jerk-focus` | main 6c, reel r5 | mens p14 | 1696 x 605 | 958 px (8.5 pt) | 1147 px (7.1 pt) |
| `s06-drills` | main 6c | mens p14 | 1697 x 831 | 958 px (8.5 pt) | 1147 px (7.1 pt) |
| `s06-inside-each-window` | main 6d | mens p144 | 1697 x 1109 | 958 px (8.5 pt) | 1147 px (7.1 pt) |
| `s07-metconx-mens` | main 7a | mens p6 | 1697 x 989 | 958 px (8.5 pt) | 1147 px (7.1 pt) |
| `s07-metconx-womens` | main 7a (correction 7) | womens p6 | 1697 x 989 | 958 px (8.5 pt) | 1147 px (7.1 pt) |
| `s07-where-time-goes` | main 7a | mens p20 | 1697 x 1095 | 958 px (8.5 pt) | 1147 px (7.1 pt) |
| `s07-db-bench` | main 7b SkillCard 2, reel r6 | mens p21 | 1673 x 373 | 854 px (9.4 pt) | 854 px (9.4 pt) |
| `s07-sandbag-carry` | main 7b SkillCard 3, reel r6 | mens p21 | 1653 x 372 | 844 px (9.4 pt) | 844 px (9.4 pt) |
| `s08-run-pace` | main 8b | mens p16 | 1696 x 711 | 958 px (8.5 pt) | 1147 px (7.1 pt) |
| `s09-week2-monday` | main 9 background, 25% | mens p53 | 2100 x 2999 | texture |  |
| `s10-heavy-strength` | main 10b | mens p79 | 1752 x 1209 | 1255 px (6.7 pt) | 1502 px (5.6 pt) |
| `s10-athx-triangle` | main 10b | mens p54 | 1748 x 1066 | 1252 px (6.7 pt) | 1498 px (5.6 pt) |
| `s10-run-and-ski` | main 10b | mens p90 | 1761 x 1015 | 1262 px (6.7 pt) | 1509 px (5.6 pt) |
| `s10-cover-mens` | main 10c, reel r7 | mens cover wrap | 2099 x 2999 | cover |  |
| `s10-cover-womens` | main 10c, reel r7 | womens cover wrap | 2099 x 2999 | cover |  |

### How the crops are made (correction 9)

`pipeline/crops.json` names each element by its **first and last line of text**,
never by coordinates. `pipeline/resolve_crops.py` then:
- finds those lines with `pdftotext -bbox`;
- snaps outwards on the 300 dpi render until 28 px (about 6.7 pt) of clear paper
  on every side, so fills, rules and the orange edge bars are inside however far
  they reach past the text;
- adds the scope's 8 px margin, checks that margin is clear paper, and fails
  rather than guess if it is not.

It writes the pixel box back into `crops.json`, and a full regenerate reproduces
it byte for byte. `--grid ID` draws any crop on a 100 px coordinate grid for
checking by eye.

`pipeline/book.py` holds the page geometry:
- **Bleed:** 9 pt top, bottom and on the outside edge (right on odd pages, left on
  even); the margins alternate to match.
- **Women's page mapping (correction 2):** `book_page()`.
- **Covers:** the wraps' front panel, cut at the trim. The fore-edge accent strip
  is 70 px wide, 33 px of it inside the trim, so the cover keeps it as printed and
  no bleed shows.

`assets/cutouts/index.json` also records every text row inside each cut-out as px
boxes with its text and cells, for the row-by-row builds, highlight bands and
underlines at Gate 2. For example, the p9 table's TOTAL column cells, for the
yellow highlight in 4c.

### Decisions

- **Edition.** Men's, as brief 5.2 indexes it, except the women's p6 beside the
  men's in 7a (correction 7). See Q10.
- **SkillCard cut-outs (correction 6).**
  - Card 1 (6a): the p5 Strength Zone window table.
  - Cards 2 and 3 (7b, reel r6): p21's "The DB bench press" and "Sandbag squats
    into the carry", heading and first paragraph. Each paragraph says why the
    movement is new or hard, which is what the card's one line points at.
- **p6 crops take the heading.** "MetCon X", its edition-coloured rule and the
  one-line description (which matches VO 7a) go with the table. The tables
  themselves are grey in both editions, so the rule is what tells them apart.
- **Day pages (10b)** take the text column's width, not the page's, from just
  above the week label to the end of the session table. Cropping at the trim width
  pushed the main text's 20 px width past what the frame can show.
- **Scene 9 background:** the whole trimmed p53, marked as texture (25%), so it is
  exempt from the legibility check.
- **Run pace table (8b):** cropped whole; which three rows show is Q12. The row
  geometry is in the index either way.

### Findings

- **Editions.** Text is identical in both editions on every cut-out page except:
  - p6 (MetCon X loads);
  - p54 / women's p57 (ATHX Triangle calories and loads);
  - p53 / women's p56 (DB bench 20 kg against 12.5 kg; background only).
- **Legibility.** The book sets table text at 8.5 pt and labels at 7.1 pt, so a
  table cut-out needs about 960 px of screen width for 20 px text, 1150 px for
  its labels. One cut-out at a time works at full width. Two side by side at half
  width (852 px) give about 18 px text. The day pages (6.7 pt) need about
  1250 px. The reel's split jerk table at the 900 px safe width gives about 19 px.
  See Q11 and Q13.

### Gaps list

| Needed | For | When |
|---|---|---|
| A 30 s voiceover test from Jon (any paragraph, the real room and mic) | Tuning `clean_vo.sh` by ear before the full read; the plan's mitigation for an echoey room | Now, if possible |
| The full read: `vo-s01` to `vo-s10` (nine files) and `vo-reel.wav` | Gate 3 animatic | Gate 3 |
| One licensed music track (95 to 115 BPM, no vocals, 6 min or loopable) and its licence | Gate 3 animatic | Gate 3 |
| Volume-Progression PDF | Optional Scene 10 background | Optional |
| App screen recording of the ATHX programme | Optional Scene 10 | Optional |

### Questions

- **Q10. Edition balance.** Twelve of the sixteen book cut-outs read word for word
  the same in both editions; only the accent colour differs. With the brief's men's pages,
  orange appears in every book shot and purple only in 7a and the women's cover.
  Options:
  - (a) Keep men's throughout, as briefed.
  - (b) **Recommended:** alternate by scene, so neither edition reads as "the book":
    men's for Scenes 4, 6 and 8, women's for the 7a "Where the time goes" table,
    the 7b cards, the Scene 9 background and Scene 10b. The 10b ATHX Triangle page
    would then show the women's loads. Each is a one-word change in `crops.json`.
- **Q11. Scene 7a layout.** Men's and women's p6 side by side fit only at half
  width, where their table text is about 18 px, under the 20 px minimum. Options:
  - (a) **Recommended:** in sequence at full width. Men's builds row by row, then
    the women's replaces it with its ATHX column highlighted, then p20.
  - (b) Side by side at about 18 px, as a stated exception to the rule.
  - (c) Crop both to the ELEMENT and ATHX columns so they fit side by side at full
    size. This drops Lite and Pro and joins two separate crops, which edges
    towards rearranging the page.
- **Q12. Scene 8b, which three rows?** The brief says three rows of the run pace
  table.
  - **Recommended:** the header plus 4:30, 4:15 and 4:00 /km, contiguous rows
    where mid-pack athletes sit. They show each 15 s per km buying about 45 s more
    ski. The component masks to them; nothing is re-cut.
- **Q13. Small print inside cut-outs.** Column headings and labels (5.6 to 7.1 pt)
  fall under 20 px wherever the main text only just reaches it: the day pages, and
  any half-width layout. The reel's split jerk table is about 19 px main text at
  the 9:16 safe width.
  - **Recommended:** apply the 20 px rule to each cut-out's main text, treat
    headings and labels as context, and accept the reel table at 19 px.

---

## Gate 0 addendum 3: colour interiors, answers, own repo (2026-10-29)

**Colour interiors received and passing.** `ATHX-2027-Mens.pdf` (158 pages) and
`ATHX-2027-Womens.pdf` (161 + the blank padding page) are RGB colour.
`pipeline/check_pdfs.sh` exits clean.
- Built 2 s before the print files and **text-identical to them on every page**, so
  the page index check and the women's +3 offset in addendum 1 hold unchanged.
- Accents match the tokens: men's `#EA580C`, women's `#7C3AED`. The men's edition
  also uses a near-black brown, `#290D03`, in small elements on pp 4, 26, 43 and
  140 with no women's counterpart. None of those pages is cut, so it is noted, not
  acted on.
- Only pp 25, 31 and 40 carry no colour.
- The greyscale `-print` copies are removed from `assets/pdf/`; the uploads remain.

**What the colour pages showed.**
- **p6 confirms decision 13.** The ATHX column reads DB 20 kg, sandbag 50 kg, row
  45 cal (men's) and 12.5 kg, 30 kg, 35 cal (women's).
- **Scene 7 crops include the heading.** The p6 tables are neutral grey in both
  editions; the edition colour is only on the "MetCon X" heading rule and the
  bullets. Each crop takes the heading and its rule, so the two tables side by
  side read as men's and women's.
- **The run note.** The book (p5) says the run is "2.4 km for Lite, 3 km for ATHX
  and Pro", where the fact sheet says "Lite 2.4 km for pairs". Not on screen;
  noted in `facts.ts`.

**Answers.**
- **Q5, 69 minutes: (a).** HybridX confirms 69 for 2027 as 20 + 24 + 25. The book
  agrees on 69 as total working time (pp 33, 87, 138), and p5 says individuals
  lift for fifteen minutes and pairs twenty.
  - The ATHX day timeline draws and labels its blocks from
    `facts.athx.clock.zoneSlotMinutes` (20, 24, 25), so they add to the 69 on the
    3c card.
  - The Strength windows stay 3 x 5 minutes (6a, the 3b card).
  - The exact strength label is Gate 2 copy, shown on the stills for approval.
- **Q6, copy trims: approved.** 3c HYROX card: "1 RACE, ABOUT 60 TO 100 MIN",
  small print "Most age-group athletes, start to finish". Scene 8 caption:
  "3 KM RUN. ONLY SKI METRES SCORE".
- **Q9, reel r2: approved.** "...in about two and a half hours" stands. The seven
  reel lines go into Jon's recording session as one extra WAV, `vo-reel.wav`.
- **Q4, own repo: done.** The session's GitHub integration cannot create a
  repository (403), so HybridX created `xhybrid-dev/athx2027`, which also fits the
  scope's other two videos, both ATHX 2027.
  - The project's full history (4 commits) moved across with `git subtree split`,
    with the project at the repo root, on `main`.
  - A bootstrap from a fresh clone passed: npm ci, checks, 1 s render, all four PDFs.
  - The `hybridx-video/` folder in the website repo is retired. It only ever lived
    on the website branch `claude/hyrox-athx-video-gate0`, never on `master`, and
    that branch can be deleted.
- `CLAUDE.md` added, so a session opened on the new repo starts with the working
  rules and the bootstrap.

---

## Gate 0 addendum 2: brand, covers and the cut-down (2026-10-29)

**Brand yellow: `#FBD85B`** (Jon: "typically the yellow used"). Set in
`tokens.ts` as `colour.accent`. The website's CSS uses `#FADB5C`, at most 3 levels
per channel away and indistinguishable on screen, so nothing on the site needs to
change for the two to match.

**White logo.** `assets/brand/hybridx-logo-full-white.png`: the full lock-up, 1400 x
785, `#ECECEC` on transparent. That is the same geometry as the site's black
`Full Logo (2).png`, so it is the reversed official file. It is used unmodified on
the end cards. PNG only; at 1400 px wide it covers any end-card size at 1080p.

**Covers.** `ATHX-2027-Mens-COVER-white.pdf` and `ATHX-2027-Womens-COVER-white.pdf`
are full print wraps (back, spine, front on one page), not front-only files. They
replace the brief's `*-FRONT.pdf` in `check_pdfs.sh` and `bootstrap.sh`.
- Black plate, white type, edition accents exactly `#EA580C` and `#7C3AED`, the
  `mens` and `womens` tokens. RGB, vector, no images.
- The front cover is the right-hand 513 pt panel. Gate 1 crops its trim box
  (inside the 9 pt bleed) for `CoverPair`. The back and spine are not used.
- The spines match KDP's white-paper calliper (0.002252 in per page): men's 0.356 in
  for 158 pages, women's 0.365 in for 162, so the women's cover was built for the
  162-page print file including its blank page.

**9:16 cut-down in scope** (Jon: "longer form landscape video and short portrait
video"). Both deliverables in scope 9 are now planned:
- `sceneTimings.ts` now holds two plans, `main` and `reel`, with one conform engine.
  `reel` is brief Part 4, seven beats from 0:00 to 1:02, target 0:55 to 1:05.
  Compositions read `timelines.main` and `timelines.reel`. Main-video numbers are
  unchanged.
- `npm run check` checks both. Reel: 79 words, 0:31 of speech at 150 wpm. r1 and
  r2 are about a second short once padded; r4 and r5 carry 6 s of graphic time each
  that a VO-led cut would close (projected 0:51). As with the main video, Gate 2's
  measured build lengths set the floors.
- The reel's VO lines are its own, not lifted from the main script, and are not in
  PRODUCTION-PLAN.md's recording script: one extra WAV, `vo-reel.wav`, seven lines
  with the same two-second gaps. See Q9.
- Gate 1 crops: nothing extra. The reel reuses the split jerk table and both covers.
- `RenderTestPortrait` (1080 x 1920) added beside `RenderTest`; both render.

**Craft note for Gate 2.** The portrait test card broke a line between "69" and
"min". Components will join every number to its unit with a non-breaking space.

---

## Gate 0 addendum: the print PDFs (2026-10-29)

Received `ATHX-2027-Mens-print.pdf` and `ATHX-2027-Womens-print.pdf`. Both were
built by ReportLab on 2026-10-28 at 513 x 738 pt (a 7 x 10 in trim with bleed).
They are newer than the copies in Drive (2026-08-29, 416 KB and 421 KB). Both
are stored in `assets/pdf/` under their own names, gitignored, not renamed,
because they are not the colour interiors.

| Check | Men's | Women's |
|---|---|---|
| Pages | 158, as expected | 162 = 161 content + 1 blank padding page (p162 is pure white) |
| Colour | **Greyscale throughout** | **Greyscale throughout** |

- **Colour.** All 158 + 162 pages render with zero chroma. The content streams
  set colour through RGB operators, but all 14 distinct values are neutral greys
  (#000000 to #FFFFFF); no images, no CMYK. Where the colour editions would carry
  the men's orange or women's purple, these use black. They are clean,
  legible black-on-white pages, but not what brief 2.4 asks for.
- **Women's offset (correction 2) confirmed exactly.** A page-by-page text
  alignment matches p1 to p42 one-for-one. Women's p43 to p45 are the added
  Chapter 13, "Aligning the Block". Men's p43 to p158 equal women's p46 to p161
  (+3). From the Taper onwards the women's chapter numbers are one higher (men's
  Ch 14 "The Compressed Warm-Up" is women's Ch 15), which matters only if a cut-out
  shows a chapter number.
- **Page index verified against the men's book.** Every page in brief 5.2 holds
  what the brief says. Correction 1 confirmed: p14 holds "Earn the load", the split
  jerk focus by week table and "The drills" table; p15 holds "If your split jerk is
  not ready in time" and the competition rules.
- **`check_pdfs.sh` reworked.** It now checks every PDF in the folder whatever its
  name, scans every page at 20 dpi rather than a sample, and lists the distinct RGB
  values. It counts trailing blank pages so print padding does not fail the page
  count, and it fails a book interior that is not in colour.

**Q8. Colour interiors.** These PDFs cannot be used for cut-outs as the brief
specifies. Two ways forward:
- (a) **Recommended.** Export the colour interiors from the same build (2026-10-28),
  so the page numbers verified above still hold. If the colour export drops the
  bleed, crop coordinates differ from the print files, but Gate 1 measures every
  crop from the PDF's own text boxes (correction 9), so that costs nothing.
- (b) Proceed with the greyscale print files as the cut-out source. They read
  cleanly as white paper on the near-black plate, but the edition colours are lost.
  The men's and women's p6 tables in Scene 7 would then be told apart only by their
  footers or by a label we add.

---

## Gate 0: Setup (2026-10-29)

### Environment

| Check | Result |
|---|---|
| OS | Ubuntu 24.04.5, 4 vCPU, 15 GB RAM, 16 GB /dev/shm, 29 GB disk free |
| Node | v22.22.0 |
| FFmpeg | 6.1.1, with loudnorm, ebur128, deesser, afftdn, acompressor, alimiter, sidechaincompress |
| Poppler | pdftoppm, pdfinfo, pdfimages, pdftotext present |
| ImageMagick, Python 3, Pillow | present (Pillow 12.3) |
| Chrome | Playwright's chrome-headless-shell 153.0.8010.12; every library resolves |
| Remotion | 4.0.539 |
| Render test | 25 frames, 1920 x 1080, H.264 High, yuv420p, bt709, 25 fps, 1.000 s (`out/tests/render-test.mp4`, still in `out/stills/render-test.png`) |

### Decisions

1. **Project location.** Superseded: the project now lives in its own repo,
   `xhybrid-dev/athx2027` (addendum 3). As first set up: `hybridx-video/` at the root of the website repo,
   self-contained (own `package.json`, `tsconfig.json`, `node_modules`). The root
   `tsconfig.json` and `vitest.config.ts` now exclude it. Without that, the site's
   `next build` typecheck would pick up the Remotion files on App Hosting, where
   their dependencies are not installed. Nothing in it is deployed.
2. **What is not in git.** Book PDFs (paid product), page renders, cut-outs,
   voiceover, music, footage and renders are gitignored. All except the PDFs and
   audio are regenerated by the pipeline. Fonts (OFL) and the scripts are tracked.
3. **Brand yellow, provisional: `#FADB5C`.** Superseded: `#FBD85B` confirmed,
   see addendum 2.
4. **Fonts.** The Google Fonts variable builds of Space Grotesk and Inter, from
   github.com/google/fonts, with their OFL licences, in `assets/fonts/`. These are
   the same files hybridx.club serves through `next/font/google`, so the video and
   site set type identically. They render the scope's four weights (Space Grotesk
   500/700, Inter 400/600) from two files rather than the four static TTFs the scope
   names. No fontTools here to cut statics; if you have house static files, drop
   them in and change `src/fonts.ts`.
5. **Browser.** Remotion's own Chrome download is blocked from this container
   (its CDN returns 403). `remotion.config.ts` uses Playwright's pre-installed
   headless shell instead, found by globbing `/opt/pw-browsers`, and
   `REMOTION_BROWSER_EXECUTABLE` overrides it.
6. **Headless stability (correction 11).** Remotion already launches Chrome with
   `--no-sandbox`, `--disable-setuid-sandbox` and `--disable-dev-shm-usage`, and
   multi-process Chrome is its Linux default, so a small `/dev/shm` (Docker's
   64 MB) is handled without extra flags. Added: `swangle` GL (software ANGLE, no
   GPU here), a 60 s delayRender timeout, and concurrency of min(vCPU - 1,
   RAM / 1.5 GB), which is 3 tabs here. `REMOTION_CONCURRENCY` overrides it; a
   proper `remotion benchmark` waits for real components at Gate 2.
7. **Delivery format (correction 11).** 1920 x 1080 H.264 (High profile,
   yuv420p, bt709), CRF 16, preset medium, JPEG intermediate frames at quality 95.
   No 4K ProRes master: this video is all graphics, so 4K gains nothing. If fine
   text shows ringing at Gate 4, render the final with `--image-format=png`.
8. **Public folder is `assets/`**, so components use `staticFile('cutouts/x.png')`.
   Remotion copies it into each render bundle; at this project's size that is
   seconds. Revisit if the page renders grow large.
9. **Timings model (correction 5).** `src/data/sceneTimings.ts` holds the
   storyboard as planned, in m:ss, with every retime from correction 5. `npm run
   check` asserts each retime and the brief's YouTube chapters exactly.
   Compositions read `timelines.main` (and, since addendum 2, `timelines.reel`),
   which conform to the recorded VO:
   - Until `src/data/voTimings.json` holds a paragraph, its shots keep their planned length.
   - Once it does, shots carrying that paragraph are cut to *lead 0.4 s + speech + tail 1.8 s*.
     The tail is the 1.5 s hold plus a breath; 5b uses 3 s because the brief holds the finished map for 3 s.
   - A shot is never cut below its `minSeconds`, and every later cut ripples.
   - Shots sharing a paragraph (1a to 1c) scale together.
   - Chapters are derived from the conformed timeline.
   - Scene dissolves are centred on the boundaries, so they never change the running time.
10. **VO-keyed builds.** Builds that land on a spoken word are cues anchored to
    that word in `voScript.ts`: the carry-over lines (SkiErg, rower, Burpees,
    sandbag, dumbbell, heavy, running), the 6a windows (overhead, squat, deadlift),
    the 3b zone cards, the 7b skill cards, the Scene 9 cards (fitness, strength,
    three, less) and the 10b day pages (heavy, MetCon, engine). Before the
    recording they are placed at 150 wpm; after it, at the measured word time if
    the VO pipeline provides one, otherwise proportionally.
11. **VO script** lives in `src/data/voScript.ts`, verbatim from the plan's
    recording script (626 words), and is the source for the Gate 4 captions.
12. **The 69 minutes (correction 3).** `facts.athx.clock.onTheClockMinutes = 69`,
    with the zone slots 20 + 24 + 25 recorded beside it (source: the plan, citing
    BLK BOX). The check confirms they sum to 69 and that the strength slot equals
    the 20-minute pairs length. Individual working time derives to 64.
13. **MetCon X loads.** The fact sheet writes them as "DB 20 kg / 12.5 kg, sandbag
    50 kg / 30 kg"; stored as men / women, the order it states for the row. No
    storyboard shot shows them.
14. **PDF colour check.** `pipeline/check_pdfs.sh` + `pdf_colour.py` use three
    signals: device colour operators in the content streams (rg/k/g with operands),
    embedded image colour spaces from `pdfimages -list`, and a 50 dpi render's chroma.
    Self-tested on the four RGB PDFs in the site repo (all read RGB) and a synthetic
    CMYK file (reads CMYK).

### Corrections from the kick-off: where each one lands

| # | Correction | Status |
|---|---|---|
| 1 | Drills table from men's p14 | Gate 1, `crops.json` (6c already reads "p14 focus + drills tables") |
| 2 | Women's page = men's up to p42, then + 3 | Gate 1, a mapping function in the crop pipeline |
| 3 | 3c card "3 ZONES, 69 MIN ON THE CLOCK" | `facts.ts` done; copy built from facts at Gate 2. See Q5 |
| 4 | VO 3b "in about two and a half hours" | Done, `voScript.ts` |
| 5 | Retimes, parameterised | Done, `sceneTimings.ts`, asserted by `npm run check` |
| 6 | SkillCard component | Gate 2 |
| 7 | Women's p6 beside the men's | Gate 1 crop, Gate 2 layout |
| 8 | Scene 9 rules land yellow, settle to white | Gate 2 |
| 9 | Pixel-exact crops via `pdftotext -bbox-layout` or a grid overlay | Gate 1 |
| 10 | `deesser=i=0.4:m=0.5:f=0.5:s=o` in `clean_vo.sh` | Gate 1 |
| 11 | Headless config, 1080p H.264, `bootstrap.sh` | Done (Decisions 5 to 7) |

### Findings

1. **No yellow in the logo files.** No `assets/brand` was supplied, so I sampled
   every HybridX logo in the website repo (`public/Full Logo (2).png`,
   `public/Icon Logo.png`, `public/plan-finder/hybridx-logo-full.png`,
   `handover/.../hybridx-x-mark.jpg`). Every opaque pixel is `#131313`, zero
   saturated pixels: the marks are monochrome. The site's CSS uses `#FADB5C` 39
   times (`--accent` and `--primary` in `globals.css`, `brand.yellow` in
   `tailwind.config.ts`) and `#C8FF00` nowhere. `#FADB5C` is a warm yellow, nearer
   HYROX's own yellow than `#C8FF00` would have been. That makes "HYROX content in
   grey, yellow for HybridX highlights only" more important, not less.
2. **The logos are black only.** On a black end card they would be invisible, and
   the QA list says the official logo is used unmodified, so I will not invert it.
3. **Book PDFs are not in the container.** Your Google Drive has
   `ATHX-2027-Mens.pdf` (416,237 bytes) and three copies of `ATHX-2027-Womens.pdf`
   (421,646 bytes each). The Drive connector returns file contents as base64 text
   through the conversation, which is not a workable way to move a binary PDF.
   Small files for 158-page books, which is fine if they are all vector; the check
   will tell.
4. **Not found anywhere:** the two FRONT cover PDFs, the Volume-Progression PDF,
   any SVG logo.
5. **VO fit at 150 wpm.** The retimed shots fit the words but leave no room for
   the lead-in and the 1.5 s hold:
   - 6a to 6d, 10a to 10c, 8b and 4b are 0.2 s to 2.4 s short once padded.
   - The conform will lengthen them when the real read arrives; that is its job.
   - Going the other way, 3a (+7 s), 4a (+5 s) and 5a (+13 s) have slack that a
     VO-driven cut would close, which is why a 150 wpm read projects to 5:14.
   - The `minSeconds` floors are my estimates until the components exist. Gate 2
     replaces them with measured build lengths: the race map labels and carry-over
     map need reading time. That will lift the projection into range.
   - No decision needed now; flagged so the Gate 3 length is not a surprise.
6. **Recording dependency.** The VO pipeline will split each scene WAV into
   paragraphs at the two-second silences the brief asks for. A mid-paragraph pause
   over about 1.2 s would split a paragraph in two; the pipeline will refuse a scene
   whose paragraph count does not match the script, rather than guess.

### Questions

Answered (see the addenda): Q1 yellow `#FBD85B`; Q2 white logo; Q3 PDFs; Q5 69
minutes, option (a); Q6 copy trims approved; Q7 cut-down in scope; Q8 colour
interiors supplied; Q9 reel r2 approved.

Q4 own repo: `xhybrid-dev/athx2027`.

Open: none for Gate 0.

Not needed until Gate 3: the voiceover WAVs (`vo-s01` to `vo-s10`, plus
`vo-reel.wav`) and the licensed music track with its licence. The
Volume-Progression PDF stays optional.

## Components

None yet. Built at Gate 2; names follow scope Section 5, plus `SkillCard`.
