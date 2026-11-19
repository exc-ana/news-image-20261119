#!/usr/bin/env python3
"""News image for Thursday 19 November 2026.

Draws a one-page newspaper front page (1024x1024 PNG) summing up six
stories from 19 November 2026: GTA VI rollout, the Trump-Xi-Putin
summit, US-Iran fire in the Gulf, the Crimean Bridge strike, the
Jeffries Speaker nomination, and Anthropic's record IPO.

Everything is drawn from scratch with the standard library only:
a small hand-built stroke font, a flat RGB canvas, and a minimal
PNG encoder. No network, no clock, no randomness, so every run
writes byte-identical output.
"""

import binascii
import os
import struct
import sys
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- font
# A hand-drawn stroke font. Each glyph is a list of strokes separated
# by ";", each stroke a space-separated list of "x,y" points on a
# 7-wide by 11-tall grid (x 0..6, y 0..10). Capitals sit on y 0..8,
# lowercase x-height on y 3..8, descenders reach y 10.
FONT = {
    "A": "0,8 3,0 6,8;2,5 4,5",
    "B": "0,0 0,8;0,0 4,0 6,2 6,3 4,4 0,4;0,4 4,4 6,5 6,7 4,8 0,8",
    "C": "6,1 5,0 2,0 1,1 0,2 0,6 1,7 2,8 5,8 6,7",
    "D": "0,0 0,8;0,0 4,0 6,2 6,6 4,8 0,8",
    "E": "0,0 0,8;0,0 5,0;0,4 4,4;0,8 5,8",
    "F": "0,0 0,8;0,0 5,0;0,4 4,4",
    "G": "6,1 5,0 2,0 1,1 0,2 0,6 1,7 2,8 5,8 6,7 6,4 3,4",
    "H": "0,0 0,8;6,0 6,8;0,4 6,4",
    "I": "1,0 5,0;3,0 3,8;1,8 5,8",
    "J": "1,0 5,0;5,0 5,7 4,8 2,8 1,7",
    "K": "0,0 0,8;5,0 1,4;2,4 6,8",
    "L": "0,0 0,8;0,8 6,8",
    "M": "0,8 0,0 3,4 6,0 6,8",
    "N": "0,8 0,0 6,8 6,0",
    "O": "1,0 5,0 6,1 6,7 5,8 1,8 0,7 0,1 1,0",
    "P": "0,0 0,8;0,0 4,0 6,2 6,3 4,5 0,5",
    "Q": "1,0 5,0 6,1 6,7 5,8 1,8 0,7 0,1 1,0;4,5 6,8",
    "R": "0,0 0,8;0,0 4,0 6,2 6,3 4,5 0,5;3,5 6,8",
    "S": "6,1 5,0 2,0 1,1 0,2 0,3 1,4 5,4 6,5 6,7 5,8 2,8 1,7",
    "T": "0,0 6,0;3,0 3,8",
    "U": "0,0 0,7 1,8 5,8 6,7 6,0",
    "V": "0,0 3,8 6,0",
    "W": "0,0 1,8 3,4 5,8 6,0",
    "X": "0,0 6,8;6,0 0,8",
    "Y": "0,0 3,4 6,0;3,4 3,8",
    "Z": "0,0 6,0 0,8 6,8",
    "a": "6,3 6,8;1,3 5,3 6,4 6,7 5,8 1,8 0,7 0,4 1,3",
    "b": "0,0 0,8;0,4 3,3 5,4 6,5 6,7 5,8 2,8 0,7 0,4",
    "c": "6,4 5,3 2,3 1,4 0,5 0,7 1,8 4,8 5,7",
    "d": "6,0 6,8;0,4 3,3 5,4 6,5 6,7 5,8 2,8 0,7 0,4",
    "e": "0,5 6,5;6,5 5,3 2,3 1,4 0,5 0,6 1,8 4,8 5,7",
    "f": "4,1 3,0 2,1 2,8;0,3 4,3",
    "g": "0,4 3,3 5,4 6,5 6,7 5,8 2,8 0,7 0,4;6,4 6,9 5,10 2,10 1,9",
    "h": "0,0 0,8;0,4 2,3 4,3 5,4 6,5 6,8",
    "i": "3,3 3,8;3,0 3,1",
    "j": "4,3 4,9 3,10 2,10;4,0 4,1",
    "k": "0,0 0,8;5,3 2,5;3,5 6,8",
    "l": "3,0 3,8",
    "m": "0,8 0,4 1,3 2,3 3,4 3,8;3,4 4,3 5,3 6,4 6,8",
    "n": "0,8 0,4 2,3 4,3 5,4 6,5 6,8",
    "o": "1,3 5,3 6,4 6,7 5,8 1,8 0,7 0,4 1,3",
    "p": "0,3 0,10;0,4 3,3 5,4 6,5 6,7 5,8 2,8 0,7 0,4",
    "q": "6,3 6,10;0,4 3,3 5,4 6,5 6,7 5,8 2,8 0,7 0,4",
    "r": "0,8 0,4 1,3 3,3 5,4",
    "s": "5,4 4,3 2,3 1,4 1,5 2,6 4,6 5,7 5,8 4,8 2,8 1,7",
    "t": "3,0 3,8 2,8 4,8;1,3 5,3",
    "u": "0,3 0,7 1,8 4,8 5,7 6,6 6,3",
    "v": "0,3 3,8 6,3",
    "w": "0,3 1,8 2,5 3,8 4,5 5,8 6,3",
    "x": "0,3 6,8;6,3 0,8",
    "y": "0,3 3,8 6,3;3,8 2,10",
    "z": "0,3 6,3 0,8 6,8",
    "0": "1,0 5,0 6,1 6,7 5,8 1,8 0,7 0,1 1,0",
    "1": "2,1 3,0 3,8;1,8 5,8",
    "2": "1,1 2,0 4,0 5,1 5,3 3,5 1,7 0,8 6,8",
    "3": "1,0 5,0 6,1 6,3 5,4 1,4;5,4 6,5 6,7 5,8 1,8 0,7",
    "4": "0,0 0,4 5,4;4,0 4,8",
    "5": "5,0 1,0 0,1 0,3 1,4 4,4 5,5 5,7 4,8 1,8 0,7",
    "6": "5,1 4,0 2,0 1,1 0,3 0,7 1,8 4,8 5,7 5,5 4,4 1,4 0,5",
    "7": "0,0 6,0 3,8",
    "8": "1,0 5,0 6,1 6,3 5,4 1,4 0,3 0,1 1,0;1,4 5,4 6,5 6,7 5,8 1,8 0,7 0,5 1,4",
    "9": "0,4 0,2 1,0 4,0 5,1 6,2 6,4 5,5 1,5 0,4;6,2 6,8",
    " ": "",
    ".": "3,7 3,8",
    ",": "3,7 3,8 2,9",
    ":": "3,2 3,3;3,6 3,7",
    ";": "3,2 3,3;3,6 3,7 2,9",
    "!": "3,0 3,5;3,7 3,8",
    "?": "1,1 2,0 4,0 5,1 5,3 3,5 3,6;3,7 3,8",
    "'": "3,0 2,2",
    '"': "2,0 2,2;4,0 4,2",
    "(": "4,0 2,2 2,6 4,8",
    ")": "2,0 4,2 4,6 2,8",
    "/": "5,0 1,8",
    "-": "1,5 5,5",
    "\u2022": "2,3 4,3;2,4 4,4;2,5 4,5",
    "$": "3,0 3,8;5,1 4,0 2,0 1,1 1,3 2,4 4,4 5,5 5,7 4,8 2,8 1,7",
    "%": "5,0 1,8;1,1 2,1 2,2 1,2 1,1;4,6 5,6 5,7 4,7 4,6",
    "#": "2,0 2,8;4,0 4,8;0,3 6,3;0,6 6,6",
    "+": "3,1 3,7;0,4 6,4",
    "=": "0,3 6,3;0,6 6,6",
    "*": "3,0 3,6;0,2 6,4;6,2 0,4",
    "_": "0,8 6,8",
}


def _q(value):
    """Round a scaled grid coordinate to the nearest pixel."""
    return int(value + 0.5)


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set(self, x, y, col):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = col

    def fill_rect(self, x, y, w, h, col):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        r, g, b = col
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = r, g, b

    def thick_dot(self, x, y, t, col):
        # A t-by-t block with its corner on the point; keeps strokes
        # even and avoids double-thick joins.
        for dy in range(t):
            for dx in range(t):
                self.set(x + dx, y + dy, col)

    def line(self, x0, y0, x1, y1, t, col):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.thick_dot(x0, y0, t, col)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def glyph(self, ch, x, y, sx, sy, t, col):
        strokes = FONT.get(ch)
        if not strokes:
            return
        for stroke in strokes.split(";"):
            pts = [tuple(map(int, p.split(","))) for p in stroke.split()]
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                self.line(x + _q(ax * sx), y + ay * sy,
                          x + _q(bx * sx), y + by * sy, t, col)

    def text(self, s, x, y, sx, sy, t, col, adv):
        """Draw a string; returns the x just past its last glyph."""
        cx = x
        for ch in s:
            self.glyph(ch, cx, y, sx, sy, t, col)
            cx += adv
        return cx

    def text_width(self, s, adv):
        return len(s) * adv


def wrap(text, max_w, adv):
    """Greedy word wrap; a line's width is its char count times adv."""
    lines = []
    cur = ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if len(trial) * adv <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------ png
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path, cv):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    blob = b"\x89PNG\r\n\x1a\n"
    blob += _chunk(b"IHDR", ihdr)
    blob += _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    blob += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(blob)
    return len(blob)


# -------------------------------------------------------------- content
PAPER = (245, 240, 230)
INK = (28, 28, 28)
BODY = (51, 51, 51)
MUTED = (110, 105, 95)
NAVY = (20, 33, 61)
GOLD = (201, 162, 39)
CREAM = (245, 240, 230)
LIGHT = (216, 222, 233)
TILE = (255, 255, 255)
TILE_EDGE = (216, 210, 196)
RULE = (200, 192, 176)

# (category, colour, headline, body, source)
STORIES = [
    ("GAMING", (108, 63, 181),
     "GTA VI ROLLS OUT",
     "After a 13-year wait, GTA VI began its global rollout. "
     "Players enter Vice City.",
     "AP"),
    ("ASIA", (179, 38, 30),
     "TRUMP, XI AND PUTIN MEET",
     "Trump, Xi and Putin held a first three-way summit in "
     "Shenzhen, on the APEC sidelines.",
     "NYT"),
    ("MIDDLE EAST", (15, 118, 110),
     "TANKER HIT IN THE GULF AS US, IRAN TRADE FIRE",
     "US strikes on Qeshm Island drew Iranian fire on US bases "
     "in Kuwait and Bahrain.",
     "REUTERS / AP"),
    ("EUROPE", (29, 78, 216),
     "CRIMEAN BRIDGE HIT FOR A THIRD TIME",
     "Ukraine struck the bridge days after its road span fell, "
     "a Russian official said on 19 Nov.",
     "BBC"),
    ("UNITED STATES", (30, 58, 95),
     "JEFFRIES TO BE SPEAKER",
     "Democrats picked Jeffries as Speaker nominee. He would be "
     "the first African-American Speaker.",
     "BBC / NDTV"),
    ("BUSINESS / TECH", (21, 128, 61),
     "RECORD $79.4B IPO FOR ANTHROPIC",
     "Anthropic raised a record $79.4 billion in its IPO debut "
     "on 19 Nov, the largest IPO ever.",
     "PRESS"),
]


def build(path):
    cv = Canvas(W, H, PAPER)

    # ---- masthead ------------------------------------------------
    cv.fill_rect(0, 0, W, 120, NAVY)
    title = "19 NOVEMBER 2026"
    tw = cv.text_width(title, 38)
    cv.text(title, (W - tw) // 2, 16, 5.25, 6, 5, CREAM, 38)
    sub = "THURSDAY \u2022 WORLD NEWS IN ONE IMAGE"
    sw = cv.text_width(sub, 14)
    cv.text(sub, (W - sw) // 2, 88, 1.75, 2, 2, LIGHT, 14)
    cv.fill_rect(0, 120, W, 4, GOLD)

    # ---- story tiles: 2 columns x 3 rows -----------------------
    tile_w, tile_h = 480, 264
    pad = 16
    inner = tile_w - 2 * pad
    for idx, (cat, colour, head, body, source) in enumerate(STORIES):
        tx = 24 + (idx % 2) * (tile_w + 16)
        ty = 132 + (idx // 2) * (tile_h + 16)

        cv.fill_rect(tx, ty, tile_w, tile_h, TILE)
        cv.fill_rect(tx, ty, tile_w, 8, colour)
        # tile border (the top edge is the colour strip)
        cv.fill_rect(tx, ty + tile_h - 2, tile_w, 2, TILE_EDGE)
        cv.fill_rect(tx, ty, 2, tile_h, TILE_EDGE)
        cv.fill_rect(tx + tile_w - 2, ty, 2, tile_h, TILE_EDGE)

        # category label with a colour chip
        cv.fill_rect(tx + pad, ty + 22, 12, 12, colour)
        cv.text(cat, tx + pad + 20, ty + 20, 1.75, 2, 2, colour, 14)

        # headline, at most two lines, bold strokes
        head_lines = wrap(head, inner, 20)
        if len(head_lines) > 2:
            raise SystemExit("headline overflows tile: %r" % head)
        hy = ty + 52
        for line in head_lines:
            if cv.text_width(line, 20) > inner:
                raise SystemExit("headline line too wide: %r" % line)
            cv.text(line, tx + pad, hy, 2.625, 3, 3, INK, 20)
            hy += 34

        # rule between headline and body
        cv.fill_rect(tx + pad, ty + 132, inner, 2, RULE)

        # body, at most three lines
        body_lines = wrap(body, inner, 14)
        if len(body_lines) > 3:
            raise SystemExit("body overflows tile: %r" % body)
        by = ty + 146
        for line in body_lines:
            if cv.text_width(line, 14) > inner:
                raise SystemExit("body line too wide: %r" % line)
            cv.text(line, tx + pad, by, 1.75, 2, 2, BODY, 14)
            by += 24

        # source tag at the bottom of the tile
        cv.text("SOURCE: " + source, tx + pad, ty + 232,
                1.75, 2, 2, MUTED, 14)

    # ---- footer --------------------------------------------------
    foot = "SOURCES: AP \u2022 BBC \u2022 REUTERS \u2022 NYT \u2022 NDTV"
    fw = cv.text_width(foot, 14)
    cv.text(foot, (W - fw) // 2, 978, 1.75, 2, 2, MUTED, 14)

    return write_png(path, cv)


def main():
    # Grader runs the repo read-only in /bot and reads the image from
    # $MAKEFUN_OUTPUT_DIR/entry.png (default /output), so write there —
    # never into the repo directory. Image bytes are unchanged.
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "entry.png")
    size = build(out)
    print("wrote %s (%d bytes)" % (out, size))


if __name__ == "__main__":
    main()
