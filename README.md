[![make.fun · news-image-20261119](https://make.fun/badge/news-image-20261119.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![rank](https://make.fun/badge/news-image-20261119/exc-ana/news-image-20261119/rank.svg)](https://make.fun/bounty/news-image-20261119/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![reward](https://make.fun/badge/news-image-20261119/exc-ana/news-image-20261119/reward.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)

# Sum up 19 November 2026's world news in one image

make.fun bounty entry **program** (not a submission) for account **@exc-ana**.
Bounty: $250, ends Sat 21 Nov 2026 07:00 WIB (Sat 21 Nov 00:00 UTC).
Opened 19 Nov 2026; 50 places paid (1st $50, 50th $3).
Detail: https://make.fun/bounty/news-image-20261119

## How to run

```sh
python3 main.py
```

Writes `output.png` (1024×1024 PNG) in this folder.
Python standard library only — no third-party packages, no network
at runtime, no timestamps, no randomness.

## Output

- File: `output.png`
- Format: PNG, RGB, 1024×1024 px
- Size: **18,865 bytes** (limit: 1 MiB)
- SHA-256: `7ba43275faa64eec6c0d350f9dae3a0893d4c15f1e561d513886abae644a5b7a`

## Verification (run twice, same bytes)

```sh
python3 main.py && sha256sum output.png
cp output.png /tmp/run1.png
python3 main.py && sha256sum output.png
cmp /tmp/run1.png output.png   # -> identical
```

Result on 2026-11-19 ~13:52 WIB (after the full-day refresh): both runs
wrote 18,865 bytes with the same SHA-256 above — **determinism PASSED**.
Pillow (local check only, not used by the generator) confirms PNG
1024×1024, RGB. The image was also visually checked: the date
"19 NOVEMBER 2026" is in the header, six tiles are legible, no text
overflows its tile, and the sources line is in the footer.
(Earlier build, ~08:35 WIB: 19,076 bytes, SHA-256
`3cf934080929a13080016c9f3fae7176dc1bb8dc3f78c37f7d5ce9607414f0a5`.)

## Events shown (all from 19 November 2026)

1. **Culture / Gaming — GTA VI begins global rollout.**
   After a 13-year wait, Grand Theft Auto VI launched worldwide,
   gamers entering Vice City. Source: AP, 19 Nov 2026.
2. **Asia — Trump, Xi and Putin meet in Shenzhen.**
   The three leaders held their first three-way summit in Shenzhen
   on 19 Nov, on the APEC sidelines. Source: NYT, 19 Nov 2026.
3. **Middle East — US and Iran trade fire in the Gulf.**
   Iran widened its attacks to US bases in Kuwait and Bahrain,
   after US strikes on Qeshm Island, and a tanker was struck in
   the Strait of Hormuz. Source: Reuters / AP, 19 Nov 2026.
4. **Europe — Crimean Bridge attacked again.**
   Ukraine struck the Crimean Bridge for a third time this week,
   a Russian official said on 19 Nov, days after its road span
   fell. Source: BBC, 19 Nov 2026.
5. **United States — Jeffries set to be first Black Speaker.**
   Democrats nominated Hakeem Jeffries for House Speaker; he is set
   to be the first African-American to hold the post.
   Source: BBC / NDTV, 19 Nov 2026.
6. **Business / Tech — Anthropic IPO raises record 79.4bn.**
   Anthropic raised a record 79.4 billion in its IPO debut on
   19 Nov, the largest IPO ever. Source: press, 19 Nov 2026.

## What changed in the full-day refresh (2026-11-19 ~13:52 WIB)

- **Swapped in:** Anthropic's $79.4B IPO debut (Business/Tech
tile) **replaces** Voyager 1's one-light-day milestone. The IPO is
the day's biggest new business story; Voyager 1 was a slow-moving
milestone with no new 19 Nov development beyond the confirmation.
- **Updated wording, same stories:** Trump–Xi–Putin summit — the
three-way summit is now reported as held in Shenzhen, not merely
due; Crimean Bridge — now a third strike this week, not just
"attacked again"; US–Iran — a tanker was struck in the Strait
of Hormuz, added to the Kuwait and Bahrain attacks and Qeshm island
strikes.
- **Unchanged:** GTA VI global rollout, Jeffries as first Black
Speaker.
- **Considered but not swapped in:** Israel's president tapping Gadi
Eisenkot to form a government (bypassing Netanyahu); Australia/
Canada/Italy/UK calling on Israel to let aid reach flooded Gaza;
Russian military plane crash in Siberia (19 killed); EU
governments greenlighting the Indonesia trade pact; NSA outage
disrupting Middle East intelligence links. All are real 19 Nov
stories, but none displaced a stronger tile in the 6-tile layout;
the Gaza-aid and Eisenkot stories overlap the Middle East tile,
and the crash/pact/outage are narrower than the six kept.
- Footer sources line updated (NASA removed, since Voyager 1 left
the image).
- Early-day build for reference: 19,076 bytes, SHA-256
`3cf934080929a13080016c9f3fae7176dc1bb8dc3f78c37f7d5ce9607414f0a5`.

## Note on timing

Built from early-day reporting (about 01:30 UTC / 08:30 WIB on 19 Nov),
then refreshed with the full day's reporting on 2026-11-19 ~13:52 WIB
(see "What changed" above). Deadline is Sat 21 Nov 07:00 WIB; major
stories breaking on 20 Nov belong to the 20 Nov bounty, not this one.

## Status

- Program built and verified locally 2026-11-19 ~08:35 WIB; refreshed
with the full day's news and re-verified 2026-11-19 ~13:52 WIB.
- NOT submitted: submission still blocked on a linked Solana wallet
(Bos to connect) and a public GitHub repo for this entry.
- No repo created, no wallet linked, no money spent.
