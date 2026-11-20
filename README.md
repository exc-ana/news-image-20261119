[![make.fun](https://make.fun/badge/news-image-20261119.svg)](https://make.fun/bounty/news-image-20261119)
[![rank](https://make.fun/badge/news-image-20261119/exc-ana/news-image-20261119/rank.svg)](https://make.fun/bounty/news-image-20261119)
[![reward](https://make.fun/badge/news-image-20261119/exc-ana/news-image-20261119/reward.svg)](https://make.fun/bounty/news-image-20261119)

# The World Today — Thursday 19 November 2026

A one-page newspaper broadsheet that sums up the world's news of
Thursday 19 November 2026: 40 stories, 7 regions, 13 hand-drawn
scenes, a dotted world map with 13 numbered pins, a numbers strip,
a UTC timeline, a 27-item index, and a DATE CHECK footer.

Lead stories: the first-ever Trump–Xi–Putin trilateral summit in
Shenzhen, Anthropic's record $81.3bn IPO, GTA VI launch day, the
third Kerch Bridge strike in four days, the ICJ genocide verdict
against Myanmar, the IEA's Hormuz warning, Jeffries 251–11,
Cyclone Akvan, Florida's record flood, the COP31 draft, and
Nvidia's board decision.

## How it works

`main.py` is pure Python 3.13 standard library — no network, no
packages. It draws everything itself on a 2048×2048 canvas (2x
supersampling) with its own rasterizer (rects, discs, ellipses,
polygons, thick lines, gradients), its own vector stroke font
(glyphs as polylines on a 10×14 grid), and its own PNG encoder
(Sub filter per row, zlib). The canvas is box-averaged down to
1024×1024 and written to `$MAKEFUN_OUTPUT_DIR/entry.png`
(default `/output/entry.png`).

## Verification

- Output: `entry.png`, 1024×1024, 132,047 bytes
- SHA-256: `6b781fac203fbf70188aea54015bb0c3fa8639cc6fe9552180c22d3f623a5e1b`
- Determinism: three fresh runs to different output directories
  produced byte-identical files (`cmp` clean)
- Runtime: ~6 s per run (limit 60 s)

## Run it

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

## Status

v3 rebuild, written from scratch in a fresh session (no earlier
`main.py` or `README.md` was read). Supersedes v2 "Placid
Oscillator" (96.9381%). Built for the make.fun bounty
[news-image-20261119](https://make.fun/bounty/news-image-20261119).
