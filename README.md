# Sum up 19 November's world news in one image

Entry for the make.fun bounty **news-image-20261119** ($250, ends
Sat 21 Nov 2026 07:00 WIB / 00:00 UTC). Account: @exc-ana (Exc Ana).

## How to run

```sh
python3 main.py
```

Standard library only, no network, no clock, no randomness. It writes
`output.png` in the same folder.

## Output

- Format: PNG, RGB, 1024 x 1024 pixels
- Size: 43,064 bytes (limit: 1 MiB)
- SHA-256: `f89293f3221853021815c4ad3d5fbbf3775994ccae05875bbe76c2dee3f089b7`

## Determinism check

Ran `python3 main.py` twice in a row; both runs wrote byte-identical
`output.png` (same SHA-256 above, `cmp` clean). The program also
self-checks at runtime that every headline fits in at most 2 lines
and every body in at most 3 lines inside its tile, and exits with an
error otherwise.

## What the image shows

A newspaper front page headed "19 NOVEMBER 2026 — THURSDAY • WORLD
NEWS IN ONE IMAGE", with six tiles:

1. **Gaming** — GTA VI rolls out: after a 13-year wait, Grand Theft
   Auto VI began its global rollout; players enter Vice City. (AP)
2. **Asia** — Trump, Xi and Putin meet: first three-way summit in
   Shenzhen, on the APEC sidelines. (NYT)
3. **Middle East** — Tanker hit in the Gulf as US, Iran trade fire:
   US strikes on Qeshm Island drew Iranian fire on US bases in
   Kuwait and Bahrain. (Reuters / AP)
4. **Europe** — Crimean Bridge hit for a third time: Ukraine struck
   the bridge days after its road span fell, a Russian official said
   on 19 Nov. (BBC)
5. **United States** — Jeffries to be Speaker: Democrats picked
   Jeffries as Speaker nominee; he would be the first
   African-American Speaker. (BBC / NDTV)
6. **Business / Tech** — Record $79.4B IPO for Anthropic: raised a
   record $79.4 billion in its IPO debut on 19 Nov, the largest IPO
   ever. (Press)

Footer names the sources: AP, BBC, Reuters, NYT, NDTV.

## How it is drawn

`main.py` draws everything itself: a hand-built stroke font (each
glyph defined as line segments on a 7x11 grid), a flat RGB canvas,
and a minimal PNG encoder (zlib + CRC chunks). No image files, no
external fonts.

## Status

Not submitted. Submission is blocked on Bos linking his Solana
wallet; no GitHub repo has been created for this entry and nothing
has been pushed or submitted.
