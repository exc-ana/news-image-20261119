#!/usr/bin/env python3
"""
Sum up 19 November 2026's world news in one image.

Deterministic generator: Python standard library only, no network,
no timestamps, no randomness. Running it twice writes byte-identical
output.png (1024x1024 PNG, < 1 MiB).

Usage:  python3 main.py
Output: output.png  (in the same directory as this file)
"""

import binascii
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- font: 5x7
# Each glyph is 7 rows of 5 bits, written as strings. Text is rendered
# in upper case only, so only upper-case glyphs are needed.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    ",": ("00000", "00000", "00000", "00000", "00100", "00100", "01000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
}

# ---------------------------------------------------------------- content
# Six specific, verified events from 19 November 2026, across regions
# and fields. Wording is factual, no hype or speculation as fact.
# Refreshed 2026-11-19 ~13:52 WIB with the full day's reporting
# (was built from early-day reporting, about 01:30 UTC). One tile
# swapped in the refresh: Voyager 1 out, Anthropic IPO in.
# (tag, accent colour, headline, body)
STORIES = [
    ("CULTURE - GAMING", (91, 33, 182),
     "GTA VI BEGINS GLOBAL ROLLOUT",
     "After a 13-year wait, Grand Theft Auto VI launched worldwide "
     "on 19 Nov, with gamers entering Vice City. (AP)"),
    ("ASIA - DIPLOMACY", (180, 83, 9),
     "TRUMP, XI AND PUTIN MEET IN SHENZHEN",
     "The US, Chinese and Russian leaders held their first "
     "three-way summit in Shenzhen on 19 Nov, on the APEC "
     "sidelines."),
    ("MIDDLE EAST", (178, 34, 34),
     "US AND IRAN TRADE FIRE IN THE GULF",
     "Iran widened its attacks to US bases in Kuwait and Bahrain, "
     "after US strikes on Qeshm Island, and a tanker was struck "
     "in the Strait of Hormuz."),
    ("EUROPE - UKRAINE WAR", (30, 64, 175),
     "CRIMEAN BRIDGE ATTACKED AGAIN",
     "Ukraine struck the Crimean Bridge for a third time this "
     "week, a Russian official said on 19 Nov, days after its "
     "road span fell."),
    ("UNITED STATES", (15, 118, 110),
     "JEFFRIES SET TO BE FIRST BLACK SPEAKER",
     "Democrats nominated Hakeem Jeffries for US House Speaker; he "
     "is set to be the first African-American to hold the post."),
    ("BUSINESS - TECH", (4, 120, 87),
     "ANTHROPIC IPO RAISES RECORD 79.4BN",
     "Anthropic raised a record 79.4 billion in its IPO debut on "
     "19 Nov, the largest IPO ever."),
]

NAVY = (15, 42, 68)
GOLD = (212, 175, 55)
PAPER = (247, 243, 232)
WHITE = (255, 255, 255)
INK = (17, 24, 39)
GREY = (75, 85, 99)
BORDER = (203, 213, 225)

# ---------------------------------------------------------------- canvas
buf = bytearray([PAPER[0], PAPER[1], PAPER[2]]) * (W * H)


def fill_rect(x, y, w, h, colour):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            buf[i], buf[i + 1], buf[i + 2] = colour


def draw_text(x, y, text, scale, colour):
    """Draw upper-case text; returns width in pixels."""
    cx = x
    for ch in text.upper():
        glyph = FONT.get(ch, FONT[" "])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":
                    fill_rect(cx + col * scale, y + row * scale,
                              scale, scale, colour)
        cx += 6 * scale
    return cx - x - scale  # width without trailing spacing


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def wrap(text, max_width, scale):
    """Greedy word wrap to lines that fit max_width pixels."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- header
fill_rect(0, 0, W, 172, NAVY)
fill_rect(0, 172, W, 6, GOLD)
draw_text(32, 26, "THE WORLD IN ONE DAY", 3, GOLD)
draw_text(32, 58, "19 NOVEMBER 2026", 6, WHITE)
draw_text(32, 122, "THURSDAY - SIX STORIES, SIX REGIONS", 3, (191, 219, 254))

# ---------------------------------------------------------------- tiles
MARGIN, GAP = 32, 20
TILE_W = (W - 2 * MARGIN - GAP) // 2          # 470
TILE_H = 248
TOP = 196
for idx, (tag, accent, head, body) in enumerate(STORIES):
    col, row = idx % 2, idx // 2
    tx = MARGIN + col * (TILE_W + GAP)
    ty = TOP + row * (TILE_H + GAP)
    fill_rect(tx, ty, TILE_W, TILE_H, WHITE)
    # border
    fill_rect(tx, ty, TILE_W, 2, BORDER)
    fill_rect(tx, ty + TILE_H - 2, TILE_W, 2, BORDER)
    fill_rect(tx, ty, 2, TILE_H, BORDER)
    fill_rect(tx + TILE_W - 2, ty, 2, TILE_H, BORDER)
    # accent bar
    fill_rect(tx, ty, TILE_W, 10, accent)
    fill_rect(tx, ty + 10, 8, TILE_H - 10, accent)
    # tag
    draw_text(tx + 24, ty + 26, tag, 2, accent)
    # headline, scale 3
    y = ty + 56
    for line in wrap(head, TILE_W - 48, 3):
        draw_text(tx + 24, y, line, 3, INK)
        y += 26
    # body, scale 2
    y += 6
    for line in wrap(body, TILE_W - 48, 2):
        draw_text(tx + 24, y, line, 2, GREY)
        y += 19

# ---------------------------------------------------------------- footer
draw_text(32, 984,
          "SOURCES: AP, BBC, REUTERS, NYT - 19 NOV 2026",
          2, GREY)

# ---------------------------------------------------------------- PNG out
# Deterministic PNG: IHDR + a single IDAT (zlib level 9, fixed) + IEND.
# No tIME / text chunks, so identical input gives identical bytes.
def chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
    return out


raw = bytearray()
for yy in range(H):
    raw.append(0)  # filter: none
    raw += buf[yy * W * 3:(yy + 1) * W * 3]

ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
png = b"\x89PNG\r\n\x1a\n"
png += chunk(b"IHDR", ihdr)
png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
png += chunk(b"IEND", b"")

here = os.path.dirname(os.path.abspath(__file__))
out_path = os.path.join(here, "output.png")
with open(out_path, "wb") as f:
    f.write(png)
print("wrote %s (%d bytes, %dx%d)" % (out_path, len(png), W, H))
