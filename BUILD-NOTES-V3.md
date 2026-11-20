# Build notes — news-image-20261119 v3 ("v3", entry live: v2 "Placid Oscillator")

Built 20 Nov 2026, ~21:10–21:30 WIB, in a fresh session, on Bos's
standing instruction to keep improving toward the top 10
("tingkatkan terus ya", 21:08 WIB). Deadline Sat 21 Nov 2026
07:00 WIB. NOT submitted; parent handles repo push + resubmit.

## Design decisions

- Same winning broadsheet formula (TOP10-19NOV-RESEARCH.md), better
  execution: the v2 gap (96.9381% vs ~99% top 10) is visual, not
  content. So: same structure, refined rendering.
- 2x supersampling, own rasterizer. Pure stdlib: RGB bytearray
  canvas at 2048×2048, filled quads/circles/polygons/gradients,
  box-average downsample to 1024, hand-rolled PNG encoder
  (Sub filter per row, zlib). Full run ~6 s.
- Vector stroke font, designed fresh in this session: glyphs are
  polylines on a 10×14 grid, two characters per point
  (x in 0-9,A; y in 0-9,A-H), strokes separated by ';'. Three
  weights via stroke thickness, plus letter spacing for display
  sizes. Full charset A-Z, 0-9, punctuation — verified by rendering
  a charset test image before the first full render.
- Thirteen drawn scenes: Shenzhen summit (dusk skyline, 3 flags,
  3 seated leaders), GTA VI (Vice City sunset, palms, car),
  Anthropic IPO bar chart, ICJ Peace Palace, Kerch Bridge,
  a zoomed Strait of Hormuz inset (a new differentiator), Capitol
  dome, Gaza tanks, EU stars, Akvan spiral, Florida flood,
  COP31 globe + draft, Nvidia chip. All scene geometry is sized
  to its panel (height-based radii) so nothing bleeds.
- Facts re-derived from same-day reporting (20 Nov searches):
  Anthropic $81.34bn at $83, +34% on debut; gold $3,713
  14-month low; ICJ 9–6; Kerch third strike; Jeffries 251–11;
  Akvan 105,304 evacuated; BOJ Ueda signals a December hike
  (rate 1.25%); UK 1,000 drones £260m; EU €45bn loan;
  Van Gogh $190.4m artist record; Walmart $188.8bn;
  Denmark Greenland–US pact 109–0; US Senate rejects Iran
  war powers 51–48; Trump pardons Pete Rose; Australia jobless
  highest since 2021; South Africa holds 7.25%; markets
  S&P −0.2%, Nasdaq +0.4%, Nikkei +0.7%, Hang Seng −1.9%.

## Bugs found by visual inspection (all fixed)

1. **Display type too heavy.** Masthead at weight 1.8 merged
   adjacent letters ("THE" read as "TVE"): at size 58 the stroke
   half-width ate the 1-unit gap between glyphs. Fixed to
   weight 1.25 + 3 px letter spacing (masthead) and weight 1.35
   + 2 px spacing (date headline). Charset test re-rendered clean.
2. **Row-4 text overflow.** Six small cards: 3-line bodies spilled
   past the card frame into the numbers strip. Fixed by shrinking
   the scene (140 → 126 working px), headline 19 → 18,
   body 16 → 15.
3. **Map pins merged in Europe.** The Hague (4.3E) and Brussels
   (4.35E) share a longitude; Miami and Jacksonville nearly do.
   Nudged pin 4 (−16,−10), pin 9 (+18,+14), pin 11 (+18,−12).
4. **US flag wrong.** First version drew the US flag as solid red
   with a gold disc (same as China). Fixed: red/white stripes
   with a navy canton.
5. **GTA car too big.** First version used absolute offsets for
   the cabin, making a black smear. Rebuilt scaled to car width.
6. **Kerch smoke too big.** Grey discs read as balloons; shrunk
   and lowered.

## Compliance (explicit)

**NO main.py or README of any version was read in this session**
— not 19 Nov v1/v2, not 20 Nov, not the v3 attempt. No `cp`,
`grep`, `sed`, or `head` on those files. Files read: this
folder's TOP10-19NOV-RESEARCH.md, REBUILD-V2-NOTES.md,
transcripts/BUNDLE-COMMAND.md, kit RULES.txt (grep for badge
URLs and spec only), and `output.png` v2 for visual inspection
only. The v2 `main.py` + `README.md` + `output.png` were copied
to `/tmp/backup-19nov-v2/` (SHA-256 main-v2
`036e9f3e…`, README-v2 `3005d1c0…`, output-v2 `8736dfd7…`)
and then removed from the repo folder before writing; the v2
code is also preserved in local git history (commit `9da31f7`).

## Verification (final code)

- Run B: `MAKEFUN_OUTPUT_DIR=/tmp/v3runB` → 132,047 bytes,
  SHA-256 `6b781fac203fbf70188aea54015bb0c3fa8639cc6fe9552180c22d3f623a5e1b`
- Run C: `/tmp/v3runC` → identical bytes; Run D: `/tmp/v3runD` →
  identical bytes; `cmp` clean across all three.
- Dimensions 1024×1024, valid PNG signature, ≤ 1 MiB.
- Runtime ~6 s per run.
- Visual inspection of the final render at full size: masthead,
  date headline, all 13 cards, map + pins, numbers strip,
  timeline, index (27 items), DATE CHECK footer all legible,
  no clipped/overlapping text remaining.
- `output.png` in this folder is a copy of the verified run-B
  bytes (same SHA-256).
- Not submitted; no repo pushed; no wallet touched; no bundle
  built yet (parent bundles after this session completes, so the
  usage row exists in muse.db).
