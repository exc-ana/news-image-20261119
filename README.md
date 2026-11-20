[![make.fun · news-image-20261119](https://make.fun/badge/news-image-20261119.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![rank](https://make.fun/badge/news-image-20261119/exc-ana/news-image-20261119/rank.svg)](https://make.fun/bounty/news-image-20261119/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![reward](https://make.fun/badge/news-image-20261119/exc-ana/news-image-20261119/reward.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)

# THE WORLD TODAY — Thursday 19 November 2026

**Bounty:** [news-image-20261119](https://make.fun/bounty/news-image-20261119)
("Sum up 19 November's world news in one image", $250, closes Sat 21 Nov
2026 07:00 WIB). Entry by @exc-ana. **Status: built and verified locally,
NOT submitted.** (The previous entry, "Frank Lantern", is preserved in local
git history — see below.)

## The image

`output.png` — 1024×1024 PNG, **147,895 bytes**, SHA-256
`8736dfd72649a66de47ec9748264d7c505b0a417c720856cb4465516a09f5796`.

A one-page broadsheet, "THE WORLD TODAY", summing up Thursday 19 November
2026 in **40 stories**:

- **Lead (hero scenes, drawn in code):** the first-ever Trump–Xi–Putin
  trilateral at APEC in Shenzhen (90 minutes, no breakthrough); GTA VI
  launches on PS5 and Xbox (Vice City, Jason and Lucia, 99 on Metacritic).
- **Three cards:** Anthropic's $81.3bn IPO ($83/share, biggest ever, $1.5tn
  valuation, +30% on debut); the ICJ ruling that Myanmar committed genocide
  against the Rohingya (first such verdict against a state); the third
  Kerch Bridge strike in four days.
- **Map + four mini-cards:** dotted world map with 13 numbered pins;
  IEA on Hormuz ("largest threat in history", 2.8bn barrels lost);
  Jeffries nominated 251–11; Israeli tanks cross Gaza's Yellow Line;
  EU's €45bn Ukraine loan.
- **Four scene cards:** Cyclone Akvan, Florida's record flood (St. Johns
  River 18.05 ft, beating 1953), COP31's draft dropping fossil fuels,
  Nvidia's board refusing to reinstate Jensen Huang.
- **The day in numbers:** 90 MIN · $81.3BN · 99 · $3,713 (gold, 14-month
  low) · 18.05 FT · 251–11. Plus a UTC timeline, a 27-item index, and a red
  DATE CHECK footer naming Thursday 19 November 2026.

Every fact was re-derived by web search on 20 Nov 2026 and cross-checked
against multiple outlets (AP, Reuters, AFP, NYT, USA TODAY, Bloomberg,
ICJ, IEA, IMD, NWS). Evidence tags mark each card CONFIRMED or REPORTED.
Gold "nears $3,713, a 14-month low" is correct for 19 Nov (spot fell below
$3,700; intraday low $3,693.10, lowest since Sept 2025). Brent was ~$92.

## How it is drawn (v2 rebuild)

The v1 entry ("Frank Lantern", 96.3451%, #6,286) used a hand-made 5×7
bitmap font rendered at 1x, so its text looked like blocky pixel-art, and
its illustrations were tiny schematic pictograms. The top 10 (99.0–99.2%)
all use the same broadsheet formula, so the gap was visual execution, not
missing sections. This v2 is a from-scratch rewrite of `main.py`:

- **2x supersampling:** everything is drawn at 2048×2048 into an RGB
  buffer, then box-averaged down to 1024×1024 — real anti-aliasing on all
  text and lines (the "Crisp 2x" approach the #9 entry advertises).
- **Vector stroke font:** glyphs are polylines on a 12×16 grid, drawn as
  filled quads with round joints, in regular and bold weights — real
  typographic hierarchy (34 px masthead, 34 px date headline, 24 px lead
  heads, 15/13/12 px card heads, 11/10 px body, 8 px index).
- **Large hero scenes drawn in code:** Shenzhen dusk skyline with three
  flags and three leaders; neon Vice City sunset with palms, sun and car;
  IPO bar chart; Peace Palace; Kerch Bridge with collapsed span and smoke;
  cyclone spiral; flooded rooftop; COP31 globe; Nvidia chip.
- **Kept the winning structure:** navy masthead, red NOV 19 box, numbered
  cards, dotted world map with pins, numbers strip, UTC timeline, evidence
  tags, numbered index, red DATE CHECK footer, sources line.

## Verification

- **Determinism:** two runs to different `MAKEFUN_OUTPUT_DIR` dirs produce
  byte-identical PNGs (SHA-256 `8736dfd7…`, `cmp` clean).
- **Size/limits:** 1024×1024, 147,895 bytes (≤ 1 MiB), valid PNG.
- **Runtime:** ~2.7 s per run (grader limit 60 s).
- **Visual check:** output inspected at full size — no clipped or
  overlapping text after fixes (glyph H/t crossbar encoding, sun-ellipse
  coordinate bug, oversized cyclone/climate scenes, timeline overflow,
  GTA caption clip). Two glyph-encoding bugs found and fixed during
  inspection (see REBUILD-V2-NOTES.md).

## How to run

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py   # writes out/entry.png
# default output dir is /output/entry.png
```

Python 3 standard library only — no network, no clock, no randomness, no
external fonts or images. Deterministic by construction.

## History

- v1 "Immense Pixel" (6 stories) — submitted 20 Nov 02:36 WIB, 95.1391%.
- v1 "Frank Lantern" (40-story broadsheet) — submitted 20 Nov 04:12 WIB,
  96.3451%, #6,286. Preserved in local git: commit `167f637` ("Rewrite
  main.py from scratch in fresh session") holds the Frank Lantern
  `main.py` + `README.md`. The v2 `main.py` was written from scratch in a
  fresh session without reading those files.
- v2 (this file) — built 20 Nov 2026, not submitted. Submission (repo,
  transcript bundle, resubmit) is the parent agent's job.
