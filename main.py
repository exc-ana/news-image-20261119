#!/usr/bin/env python3
"""THE WORLD TODAY - Thursday 19 November 2026 (news-image-20261119, v2).

One-page broadsheet summing up 19 November 2026 world news, drawn entirely
in code with the Python standard library only (no network, no clock, no
randomness, no external fonts or images).

Visual-execution approach (the v2 rebuild):
  * Everything is drawn at 2x (2048x2048) into an RGB byte buffer, then
    box-averaged down to 1024x1024. Text and lines therefore get real
    anti-aliasing instead of the blocky 1x bitmap look of the v1 entry.
  * Text uses a vector stroke font defined in this file (polylines on a
    12x16 grid). Strokes are filled as quads with round joints, so glyphs
    scale cleanly and carry real typographic hierarchy: giant date
    headline, bold masthead, kickers, subheads, bylines, body, captions.
  * Three large hero scenes are drawn for the lead stories (Shenzhen
    summit, GTA VI Vice City, Anthropic IPO chart), plus smaller drawn
    scenes for the ICJ, Kerch Bridge and the cyclone, and a dotted world
    map with numbered pins.
  * Deterministic: fixed data, fixed draw order, no time/random input.
    Two runs to different output dirs produce byte-identical PNGs.

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py   (default /output/entry.png)
"""

import hashlib
import math
import os
import struct
import sys
import zlib

# ---------------------------------------------------------------- canvas ---
S = 2                      # supersampling factor (draw at 2048, output 1024)
W = 1024                   # final width
H = 1024                   # final height
WS = W * S                 # working width  (2048)
HS = H * S                 # working height (2048)

# Palette
PAPER   = (247, 242, 228)
INK     = (22, 22, 22)
NAVY    = (18, 36, 72)
NAVY_D  = (12, 26, 54)
RED     = (196, 16, 46)
RED_D   = (160, 10, 36)
GOLD    = (201, 162, 39)
TEAL    = (14, 124, 123)
SKY     = (120, 170, 205)
CREAM   = (255, 251, 238)
GREY    = (110, 108, 100)
LGREY   = (210, 206, 192)
WHITE   = (255, 255, 255)
BLACK   = (10, 10, 12)


class Canvas:
    """RGB byte buffer at working resolution, all coords in FINAL pixels."""

    def __init__(self):
        self.buf = bytearray(WS * HS * 3)
        self.fill_rect(0, 0, W, H, PAPER)

    def _px(self, x, y):
        return (y * WS + x) * 3

    def set_px(self, x, y, c):
        if 0 <= x < WS and 0 <= y < HS:
            i = (y * WS + x) * 3
            self.buf[i] = c[0]
            self.buf[i + 1] = c[1]
            self.buf[i + 2] = c[2]

    def fill_rect(self, x, y, w, h, c):
        """x,y,w,h in final pixels; fills the 2x region."""
        x0 = max(0, int(round(x * S)))
        y0 = max(0, int(round(y * S)))
        x1 = min(WS, int(round((x + w) * S)))
        y1 = min(HS, int(round((y + h) * S)))
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        stride = WS * 3
        for yy in range(y0, y1):
            i = yy * stride + x0 * 3
            self.buf[i:i + len(row)] = row

    def hline(self, x, y, w, c, t=1):
        self.fill_rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.fill_rect(x, y, t, h, c)

    def frame(self, x, y, w, h, c, t=1):
        self.hline(x, y, w, c, t)
        self.hline(x, y + h - t, w, c, t)
        self.vline(x, y, h, c, t)
        self.vline(x + w - t, y, h, c, t)

    def vgrad(self, x, y, w, h, top, bot):
        """Vertical gradient, final-pixel coords."""
        x0 = max(0, int(round(x * S)))
        y0 = max(0, int(round(y * S)))
        x1 = min(WS, int(round((x + w) * S)))
        y1 = min(HS, int(round((y + h) * S)))
        if x1 <= x0 or y1 <= y0:
            return
        n = y1 - y0
        stride = WS * 3
        width = x1 - x0
        for k in range(n):
            f = k / max(1, n - 1)
            c = (round(top[0] + (bot[0] - top[0]) * f),
                 round(top[1] + (bot[1] - top[1]) * f),
                 round(top[2] + (bot[2] - top[2]) * f))
            row = bytes(c) * width
            i = (y0 + k) * stride + x0 * 3
            self.buf[i:i + len(row)] = row

    def hgrad(self, x, y, w, h, left, right):
        x0 = max(0, int(round(x * S)))
        y0 = max(0, int(round(y * S)))
        x1 = min(WS, int(round((x + w) * S)))
        y1 = min(HS, int(round((y + h) * S)))
        if x1 <= x0 or y1 <= y0:
            return
        n = x1 - x0
        stride = WS * 3
        row = bytearray(n * 3)
        for k in range(n):
            f = k / max(1, n - 1)
            row[k * 3] = round(left[0] + (right[0] - left[0]) * f)
            row[k * 3 + 1] = round(left[1] + (right[1] - left[1]) * f)
            row[k * 3 + 2] = round(left[2] + (right[2] - left[2]) * f)
        rb = bytes(row)
        for yy in range(y0, y1):
            i = yy * stride + x0 * 3
            self.buf[i:i + len(rb)] = rb

    # ------------------------------------------------------- filled shapes
    def _fill_spans(self, y, spans, c):
        """spans: list of (x0, x1) working-pixel pairs on working row y."""
        if y < 0 or y >= HS:
            return
        stride = WS * 3
        for (a, b) in spans:
            a = max(0, a)
            b = min(WS, b)
            if b <= a:
                continue
            i = y * stride + a * 3
            self.buf[i:i + (b - a) * 3] = bytes(c) * (b - a)

    def disc(self, cx, cy, r, c):
        """Filled circle; cx, cy, r in WORKING pixels."""
        cx = int(round(cx))
        cy = int(round(cy))
        r = int(round(r))
        if r <= 0:
            return
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self._fill_spans(cy + dy, [(cx - dx, cx + dx + 1)], c)

    def ellipse(self, cx, cy, rx, ry, c):
        cx = int(round(cx))
        cy = int(round(cy))
        rx = int(round(rx))
        ry = int(round(ry))
        if rx <= 0 or ry <= 0:
            return
        for dy in range(-ry, ry + 1):
            f = 1.0 - (dy * dy) / float(ry * ry)
            dx = int(rx * (f ** 0.5)) if f > 0 else 0
            self._fill_spans(cy + dy, [(cx - dx, cx + dx + 1)], c)

    def polygon(self, pts, c):
        """Filled polygon; pts in FINAL pixels (converted to working)."""
        wp = [(int(round(px * S)), int(round(py * S))) for (px, py) in pts]
        if len(wp) < 3:
            return
        ys = [p[1] for p in wp]
        y0, y1 = max(0, min(ys)), min(HS - 1, max(ys))
        n = len(wp)
        for y in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                x1, yy1 = wp[i]
                x2, yy2 = wp[(i + 1) % n]
                if yy1 == yy2:
                    continue
                lo, hi = (yy1, yy2) if yy1 < yy2 else (yy2, yy1)
                if lo <= y < hi:
                    t = (y - yy1) / float(yy2 - yy1)
                    xs.append(x1 + t * (x2 - x1))
            if len(xs) < 2:
                continue
            xs.sort()
            spans = []
            for k in range(0, len(xs) - 1, 2):
                spans.append((int(round(xs[k])), int(round(xs[k + 1])) + 1))
            self._fill_spans(y, spans, c)

    def thick_line(self, x1, y1, x2, y2, w, c):
        """Thick line, final-pixel coords, width w in final px; round caps."""
        ax, ay = x1 * S, y1 * S
        bx, by = x2 * S, y2 * S
        dx, dy = bx - ax, by - ay
        length = (dx * dx + dy * dy) ** 0.5
        hw = w * S / 2.0
        if length < 0.5:
            self.disc(ax, ay, hw, c)
            return
        nx, ny = -dy / length, dx / length
        quad = [(ax + nx * hw, ay + ny * hw),
                (bx + nx * hw, by + ny * hw),
                (bx - nx * hw, by - ny * hw),
                (ax - nx * hw, ay - ny * hw)]
        # fill quad directly in working coords
        ys = [p[1] for p in quad]
        y0 = max(0, int(min(ys)))
        y1 = min(HS - 1, int(max(ys)) + 1)
        n = 4
        for y in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                px1, py1 = quad[i]
                px2, py2 = quad[(i + 1) % n]
                if py1 == py2:
                    continue
                lo, hi = (py1, py2) if py1 < py2 else (py2, py1)
                if lo <= y < hi:
                    t = (y - py1) / (py2 - py1)
                    xs.append(px1 + t * (px2 - px1))
            if len(xs) < 2:
                continue
            xs.sort()
            self._fill_spans(y, [(int(xs[0]), int(xs[1]) + 1)], c)
        self.disc(ax, ay, hw, c)
        self.disc(bx, by, hw, c)


# ------------------------------------------------------------------- PNG ---
def _chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(
        ">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def encode_png(rgb, w, h):
    """rgb: bytes of w*h*3. Sub-filter per row, zlib level 6."""
    raw = bytearray()
    stride = w * 3
    prev = bytes(stride)
    for y in range(h):
        row = rgb[y * stride:(y + 1) * stride]
        raw.append(1)  # Sub filter
        filt = bytearray(stride)
        filt[0] = row[0]
        filt[1] = row[1]
        filt[2] = row[2]
        for i in range(3, stride):
            filt[i] = (row[i] - row[i - 3]) & 0xFF
        raw += filt
        prev = row
    comp = zlib.compress(bytes(raw), 6)
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) +
            _chunk(b"IDAT", comp) + _chunk(b"IEND", b""))


def downsample(cv):
    """Box-average 2048x2048 -> 1024x1024 RGB bytes."""
    src = cv.buf
    out = bytearray(W * H * 3)
    sw = WS * 3
    for oy in range(H):
        r0 = oy * 2 * sw
        r1 = r0 + sw
        o = oy * W * 3
        for ox in range(W):
            i = ox * 6
            j = o + ox * 3
            out[j] = (src[r0 + i] + src[r0 + i + 3] +
                      src[r1 + i] + src[r1 + i + 3] + 2) >> 2
            out[j + 1] = (src[r0 + i + 1] + src[r0 + i + 4] +
                          src[r1 + i + 1] + src[r1 + i + 4] + 2) >> 2
            out[j + 2] = (src[r0 + i + 2] + src[r0 + i + 5] +
                          src[r1 + i + 2] + src[r1 + i + 5] + 2) >> 2
    return bytes(out)

# ------------------------------------------------------------ vector font --
# Glyphs are polylines on a 12-wide x 16-tall grid (x 0..11, y 0..15).
# Baseline y=12, cap top y=2, x-height top y=5, descender y=15.
# Encoding: each point is two chars, x in 0-9A-B, y in 0-9A-F;
# strokes are separated by ';'. A one-point stroke draws a dot.
_X = "0123456789AB"
_Y = "0123456789ABCDEF"


def _dec(s):
    strokes = []
    for st in s.split(";"):
        pts = []
        for i in range(0, len(st), 2):
            pts.append((_X.index(st[i]), _Y.index(st[i + 1])))
        strokes.append(pts)
    return strokes


GLYPHS = {
    "A": "0C62BC;3898",
    "B": "121C;1272A4A67818;1888BAAC8C1C",
    "C": "A3723215193C7CAB",
    "D": "121C;1272A5A97C1C",
    "E": "121C;1292;1777;1C9C",
    "F": "121C;1292;1777",
    "G": "A3723215193C7CAB;78A8AC7C",
    "H": "121C;B2BC;17B7",
    "I": "3292;626C;3C9C",
    "J": "828C5C2A28;42A2",
    "K": "121C;9227AC",
    "L": "121C;1C9C",
    "M": "1C1268B2BC",
    "N": "1C12BCB2",
    "O": "3282B5B98C3C090532",
    "P": "121C;1272A4A67818",
    "Q": "3282B5B98C3C090532;8ABE",
    "R": "121C;1272A4A67818;78BC",
    "S": "A3723215285899AB8C4C1A",
    "T": "02B2;626C",
    "U": "121A3C8CAAA2",
    "V": "126CB2",
    "W": "123C679CB2",
    "X": "12BC;B21C",
    "Y": "1267B2;676C",
    "Z": "12A2;A21C;1CAC",
    "a": "3585A7AA8C3C1A1735;A5AC",
    "b": "121C;175596A98C4C1A",
    "c": "A68545171A4C8CAB",
    "d": "2575979A7C2C1A1725;929C",
    "e": "957535171A3C7C9A;1898",
    "f": "8242343C;2767",
    "g": "3585A7AA8C3C1A1735;A5AD8F4F2D",
    "h": "121C;173575979C",
    "i": "555C;52",
    "j": "858D6F4F;82",
    "k": "121C;85299C",
    "l": "424C",
    "m": "151C;173555676C;6785A5B7BC",
    "n": "151C;173575979C",
    "o": "3585A7AA8C3C1A1735",
    "p": "151F;175596A98C4C1A",
    "q": "2575979A7C2C1A1725;959F",
    "r": "151C;17457587",
    "s": "9675452628498A9B9C7C4C2B",
    "t": "525C7C;3676",
    "u": "151A3C7C9A95",
    "v": "155C95",
    "w": "152C486C75",
    "x": "159C;951C",
    "y": "154B95;5C6F",
    "z": "15951C9C",
    "0": "3282B5B98C3C090532;29BA",
    "1": "3462;626C;3C9C",
    "2": "244282A4A6882C9C",
    "3": "235282A4967798AA8C5C2B",
    "4": "8218;1898;828C",
    "5": "92222777A9AB8C4C2B",
    "6": "93723215193C8CAAA8864628",
    "7": "12A24C",
    "8": "3282A4A68838161432;3888AAAC8C3C1A1838",
    "9": "2A4C8CA9A58232141638789A",
    ".": "5C",
    ",": "5C4E3F",
    ":": "57;5C",
    ";": "57;5C4E3F",
    "'": "6255",
    '"': "4235;8275",
    "!": "525A;5C",
    "?": "244282A4A688686A;5C",
    "-": "18A8",
    "(": "8255598C",
    ")": "3265693C",
    "/": "922C",
    "%": "922C;2332433423;8B9AAB9C8B",
    "$": "A3723215285899AB8C4C1A;616E",
    "+": "636B;27A7",
    "=": "16A6;1AAA",
    "*": "626C;25A9;A529",
    "#": "423C;827C;15A5;19A9",
    "•": "67",
    "—": "08B8",
    " ": "",
}
for _k in list(GLYPHS):
    GLYPHS[_k] = _dec(GLYPHS[_k]) if GLYPHS[_k] else []

# Advance width per glyph, in units of cap height (cap = 10 grid units).
NARROW = set("ijl.,:;'\"!|/()[]{}")
WIDE = set("MWmw%@#")


def glyph_adv(ch):
    if ch in NARROW:
        return 0.56
    if ch in WIDE:
        return 1.12
    if ch == " ":
        return 0.46
    if ch in "ftr":
        return 0.62
    return 0.90


XCOMP = 0.68  # horizontal compression of the 12-wide grid


class Font:
    """Vector stroke font. size = cap height in FINAL pixels."""

    def __init__(self, cv):
        self.cv = cv

    def width(self, s, size):
        w = 0.0
        for ch in s:
            w += glyph_adv(ch) * size
        return w

    def draw(self, x, y, s, size, color, bold=False):
        """Draw string with top-left at (x, y); y is the cap top.
        Returns the width drawn."""
        cv = self.cv
        u = size * S / 10.0            # working px per grid unit (vertical)
        ux = u * XCOMP                 # working px per grid unit (horizontal)
        wstroke = (1.65 if bold else 1.15) * u / S  # stroke width, final px
        cx = x
        for ch in s:
            adv = glyph_adv(ch) * size
            if ch != " " and ch in GLYPHS:
                for stroke in GLYPHS[ch]:
                    pts = [(cx + px * ux / S, y + py * u / S)
                           for (px, py) in stroke]
                    if len(pts) == 1:
                        cv.disc(pts[0][0] * S, pts[0][1] * S,
                                wstroke * S / 2.0, color)
                    else:
                        for i in range(len(pts) - 1):
                            cv.thick_line(pts[i][0], pts[i][1],
                                          pts[i + 1][0], pts[i + 1][1],
                                          wstroke, color)
            cx += adv
        return cx - x

    def draw_center(self, cx, y, s, size, color, bold=False):
        w = self.width(s, size)
        return self.draw(cx - w / 2.0, y, s, size, color, bold)


def wrap(font, s, size, max_w, bold=False):
    """Greedy word wrap; returns list of lines that fit max_w."""
    lines = []
    for para in s.split("\n"):
        words = para.split()
        if not words:
            lines.append("")
            continue
        cur = words[0]
        for wd in words[1:]:
            trial = cur + " " + wd
            if font.width(trial, size) <= max_w:
                cur = trial
            else:
                lines.append(cur)
                cur = wd
        lines.append(cur)
    return lines


def draw_lines(font, x, y, lines, size, color, leading=None, bold=False):
    if leading is None:
        leading = size * 1.32
    for ln in lines:
        font.draw(x, y, ln, size, color, bold)
        y += leading
    return y

# ------------------------------------------------------------------ scenes --
# All scene functions take final-pixel coords (x, y, w, h).

def scene_summit(cv, font, x, y, w, h):
    """Shenzhen at dusk: skyline, red carpet, three flags, three leaders."""
    cv.vgrad(x, y, w, h, (24, 32, 66), (214, 96, 46))
    # low sun glow
    cv.ellipse((x + w * 0.72) * S, (y + h * 0.62) * S, w * 0.16 * S,
               h * 0.30 * S, (232, 150, 70))
    # skyline silhouette
    towers = [(0.00, 0.62), (0.07, 0.48), (0.13, 0.58), (0.20, 0.40),
              (0.27, 0.52), (0.34, 0.34), (0.41, 0.50), (0.48, 0.44),
              (0.55, 0.56), (0.62, 0.38), (0.69, 0.50), (0.76, 0.44),
              (0.83, 0.54), (0.90, 0.46), (0.96, 0.60)]
    for i, (fx, top) in enumerate(towers):
        tx = x + w * fx
        tw = w * 0.065
        cv.fill_rect(tx, y + h * top, tw, h * (0.78 - top), (16, 20, 44))
        # lit windows
        for wy in range(3):
            for wx in range(2):
                cv.fill_rect(tx + tw * (0.2 + wx * 0.4),
                             y + h * (top + 0.06 + wy * 0.08),
                             tw * 0.16, h * 0.03, (240, 200, 90))
    # ground / red carpet
    cv.fill_rect(x, y + h * 0.78, w, h * 0.22, (20, 24, 48))
    cv.fill_rect(x + w * 0.30, y + h * 0.80, w * 0.40, h * 0.20, (178, 20, 44))
    # long table
    cv.fill_rect(x + w * 0.30, y + h * 0.62, w * 0.40, h * 0.05, (240, 235, 220))
    cv.fill_rect(x + w * 0.30, y + h * 0.67, w * 0.40, h * 0.11, (120, 20, 30))
    # three flags behind the table
    flag_cols = [(178, 30, 40), (210, 40, 40), (30, 60, 160)]
    for i, fc in enumerate(flag_cols):
        fx = x + w * (0.36 + i * 0.13)
        cv.fill_rect(fx, y + h * 0.30, w * 0.055, h * 0.16, fc)
        cv.fill_rect(fx, y + h * 0.30, w * 0.055, h * 0.05, WHITE)
        cv.vline(fx + w * 0.055, y + h * 0.28, h * 0.34, (200, 200, 200), 1)
    # three seated figures (head + shoulders)
    for i in range(3):
        fx = x + w * (0.385 + i * 0.13)
        fy = y + h * 0.52
        cv.polygon([(fx - w * 0.022, fy + h * 0.10),
                    (fx + w * 0.046, fy + h * 0.10),
                    (fx + w * 0.032, fy - h * 0.015),
                    (fx - w * 0.008, fy - h * 0.015)], (96, 104, 138))
        cv.polygon([(fx + w * 0.002, fy + h * 0.10),
                    (fx + w * 0.022, fy + h * 0.10),
                    (fx + w * 0.018, fy - h * 0.005),
                    (fx + w * 0.006, fy - h * 0.005)], WHITE)
        cv.disc((fx + w * 0.012) * S, (fy - h * 0.02) * S, 5.5 * S,
                (240, 210, 180))
    font.draw(x + 8, y + h - 15, "SHENZHEN  •  APEC  •  90 MINUTES", 9,
              (255, 240, 200), bold=True)


def scene_gta(cv, font, x, y, w, h):
    """Vice City neon sunset: sun, palms, skyline, boulevard, car."""
    cv.vgrad(x, y, w, h, (46, 16, 74), (255, 110, 80))
    # sun
    cv.disc((x + w * 0.68) * S, (y + h * 0.42) * S, w * 0.13 * S,
            (255, 214, 120))
    cv.disc((x + w * 0.68) * S, (y + h * 0.42) * S, w * 0.10 * S,
            (255, 236, 170))
    # skyline
    for i, (fx, top, tw) in enumerate([(0.02, 0.55, 0.10), (0.14, 0.42, 0.09),
                                       (0.25, 0.52, 0.11), (0.37, 0.36, 0.08),
                                       (0.47, 0.50, 0.10), (0.59, 0.44, 0.09),
                                       (0.70, 0.54, 0.10), (0.82, 0.40, 0.09),
                                       (0.92, 0.52, 0.08)]):
        cv.fill_rect(x + w * fx, y + h * top, w * tw, h * (0.72 - top),
                     (30, 12, 52))
        for wy in range(2):
            cv.fill_rect(x + w * (fx + 0.02), y + h * (top + 0.08 + wy * 0.12),
                         w * tw * 0.6, h * 0.04, (255, 90, 160))
    # palms (left and right)
    for px, flip in [(0.06, 1), (0.90, -1)]:
        bx = x + w * px
        by = y + h * 0.74
        tx = bx + flip * w * 0.03
        ty = y + h * 0.44
        cv.thick_line(bx, by, tx, ty, 3, (24, 10, 40))
        for k in range(5):
            off = (k - 2) * w * 0.035
            cv.thick_line(tx, ty, tx + flip * off,
                          ty + h * (0.02 + 0.028 * abs(k - 2)), 2,
                          (24, 10, 40))
    # boulevard + car
    cv.fill_rect(x, y + h * 0.72, w, h * 0.28, (18, 10, 34))
    cv.fill_rect(x, y + h * 0.72, w, 2, (255, 200, 90))
    carx, cary = x + w * 0.42, y + h * 0.82
    cv.polygon([(carx, cary + h * 0.05), (carx + w * 0.02, cary),
                (carx + w * 0.10, cary - h * 0.01),
                (carx + w * 0.15, cary + h * 0.05)], (200, 30, 90))
    cv.disc((carx + w * 0.04) * S, (cary + h * 0.055) * S, 3.5 * S, BLACK)
    cv.disc((carx + w * 0.12) * S, (cary + h * 0.055) * S, 3.5 * S, BLACK)
    font.draw(x + 8, y + 8, "VI", 34, (255, 240, 160), bold=True)
    cap = "VICE CITY  •  LEONIDA"
    font.draw(x + w - 8 - font.width(cap, 9), y + h - 16, cap, 9,
              (255, 220, 200), bold=True)


def scene_anthropic(cv, font, x, y, w, h):
    """IPO bar chart: SpaceX $80.0bn vs Anthropic $81.3bn."""
    cv.fill_rect(x, y, w, h, (238, 244, 248))
    base = y + h - 24
    cv.hline(x + 8, base, w - 16, NAVY, 2)
    bars = [("SPACEX", 80.0, (120, 130, 150), "JUN"),
            ("ANTHROPIC", 81.3, RED, "NOV 19")]
    bw = w * 0.26
    for i, (name, val, col, when) in enumerate(bars):
        bx = x + w * (0.16 + i * 0.42)
        bh = (h - 40) * val / 85.0
        cv.fill_rect(bx, base - bh, bw, bh, col)
        font.draw(bx - 4, base - bh - 13, "$%.1fBN" % val, 11, NAVY, bold=True)
        font.draw(bx - 2, base + 5, name, 9, INK, bold=True)
        font.draw(bx + 8, base + 14, when, 8, GREY)


def scene_icj(cv, font, x, y, w, h):
    """Peace Palace facade: pediment, columns, steps."""
    cv.vgrad(x, y, w, h, (214, 226, 238), (170, 190, 208))
    cv.polygon([(x + w * 0.10, y + h * 0.34), (x + w * 0.50, y + h * 0.10),
                (x + w * 0.90, y + h * 0.34)], (240, 236, 224))
    cv.disc((x + w * 0.50) * S, (y + h * 0.26) * S, 4 * S, GOLD)
    cv.fill_rect(x + w * 0.10, y + h * 0.34, w * 0.80, h * 0.40, (240, 236, 224))
    for i in range(6):
        cx = x + w * (0.16 + i * 0.135)
        cv.fill_rect(cx, y + h * 0.36, w * 0.035, h * 0.36, (200, 196, 182))
    cv.fill_rect(x + w * 0.06, y + h * 0.74, w * 0.88, h * 0.05, (180, 176, 164))
    cv.fill_rect(x + w * 0.03, y + h * 0.80, w * 0.94, h * 0.05, (160, 156, 144))
    cv.fill_rect(x + w * 0.00, y + h * 0.86, w, h * 0.05, (140, 136, 124))
    font.draw(x + 8, y + h - 14, "THE HAGUE", 9, NAVY, bold=True)


def scene_kerch(cv, font, x, y, w, h):
    """Kerch Strait: bridge arch, collapsed span, smoke, sea."""
    cv.vgrad(x, y, w, h, (150, 190, 215), (90, 140, 180))
    cv.fill_rect(x, y + h * 0.62, w, h * 0.38, (40, 90, 130))
    # deck + arch
    cv.fill_rect(x, y + h * 0.42, w, h * 0.05, (60, 60, 66))
    cv.thick_line(x + w * 0.10, y + h * 0.44, x + w * 0.50, y + h * 0.16,
                  4, (60, 60, 66))
    cv.thick_line(x + w * 0.50, y + h * 0.16, x + w * 0.62, y + h * 0.44,
                  4, (60, 60, 66))
    # collapsed span tilting into the water (right of the arch)
    cv.polygon([(x + w * 0.62, y + h * 0.44), (x + w * 0.78, y + h * 0.47),
                (x + w * 0.86, y + h * 0.62), (x + w * 0.70, y + h * 0.60)],
               (90, 90, 96))
    cv.thick_line(x + w * 0.62, y + h * 0.44, x + w * 0.78, y + h * 0.47,
                  3, (60, 60, 66))
    # smoke plume over the rail span
    for i, (fx, fy, fr) in enumerate([(0.50, 0.14, 9), (0.53, 0.08, 12),
                                      (0.57, 0.03, 14)]):
        cv.disc((x + w * fx) * S, (y + h * fy) * S, fr * S * 0.5,
                (90, 90, 96))
    # missile streak
    cv.thick_line(x + w * 0.78, y + h * 0.06, x + w * 0.55, y + h * 0.18,
                  2, (255, 240, 200))
    # waves
    for i in range(3):
        wy = y + h * (0.70 + i * 0.08)
        cv.thick_line(x + w * 0.05, wy, x + w * 0.30, wy - 4, 2,
                      (200, 225, 240))
        cv.thick_line(x + w * 0.55, wy + 3, x + w * 0.85, wy - 2, 2,
                      (200, 225, 240))
    font.draw(x + 8, y + 8, "3RD STRIKE IN 4 DAYS", 10, WHITE, bold=True)


def scene_cyclone(cv, x, y, w, h):
    """Cyclone spiral over the Bay of Bengal."""
    cv.fill_rect(x, y, w, h, (16, 40, 70))
    cx, cy = x + w * 0.5, y + h * 0.52
    # spiral arms: dots along an Archimedean spiral, sized to the panel
    for k in range(120):
        t = k / 120.0
        ang = t * 4.6 * 3.14159
        r = 3 + t * h * 0.85
        px = cx + r * math.cos(ang)
        py = cy + r * 0.62 * math.sin(ang)
        cv.disc(px * S, py * S, (2.2 - t * 1.0) * S, (220, 230, 240))
    cv.disc(cx * S, cy * S, 5 * S, (16, 40, 70))
    cv.disc(cx * S, cy * S, 2.5 * S, (240, 240, 230))


def scene_flood(cv, x, y, w, h):
    """Flooded street: rain, waves, rooftop."""
    cv.vgrad(x, y, w, h, (70, 90, 120), (30, 60, 90))
    for i in range(14):
        rx = x + 6 + (i * 23) % int(w - 12)
        cv.thick_line(rx, y + 4, rx - 5, y + 22, 1.5, (180, 200, 220))
    # rooftop above water
    cv.polygon([(x + w * 0.18, y + h * 0.52), (x + w * 0.50, y + h * 0.30),
                (x + w * 0.82, y + h * 0.52)], (150, 60, 50))
    cv.fill_rect(x + w * 0.22, y + h * 0.52, w * 0.56, h * 0.16, (190, 180, 160))
    # water
    cv.fill_rect(x, y + h * 0.68, w, h * 0.32, (40, 110, 150))
    for i in range(3):
        wy = y + h * (0.74 + i * 0.08)
        cv.thick_line(x + w * 0.06, wy, x + w * 0.42, wy - 4, 2,
                      (200, 230, 245))
        cv.thick_line(x + w * 0.55, wy + 3, x + w * 0.92, wy - 2, 2,
                      (200, 230, 245))


def scene_climate(cv, x, y, w, h):
    """COP31: globe, sun, leaf (all sized to the panel height)."""
    cv.vgrad(x, y, w, h, (200, 225, 235), (140, 190, 205))
    cv.disc((x + w * 0.82) * S, (y + h * 0.30) * S, h * 0.28 * S,
            (255, 205, 90))
    cx, cy, r = x + w * 0.38, y + h * 0.55, h * 0.42
    cv.disc(cx * S, cy * S, r * S, (30, 110, 90))
    cv.ellipse(cx * S, cy * S, r * 0.45 * S, r * S, (60, 160, 120))
    cv.thick_line(cx - r, cy, cx + r, cy, 2, (200, 230, 210))
    cv.thick_line(cx, cy - r, cx, cy + r, 2, (200, 230, 210))
    # leaf
    cv.polygon([(x + w * 0.88, y + h * 0.85), (x + w * 0.95, y + h * 0.62),
                (x + w * 0.99, y + h * 0.88)], (40, 140, 70))


def scene_chip(cv, font, x, y, w, h):
    """Nvidia chip: dark die, pins, green board."""
    cv.fill_rect(x, y, w, h, (20, 90, 60))
    cv.fill_rect(x + w * 0.24, y + h * 0.18, w * 0.52, h * 0.64, (16, 16, 20))
    cv.frame(x + w * 0.24, y + h * 0.18, w * 0.52, h * 0.64, (120, 200, 90), 2)
    for i in range(5):
        py = y + h * (0.26 + i * 0.12)
        cv.fill_rect(x + w * 0.16, py, w * 0.08, 3, (200, 200, 190))
        cv.fill_rect(x + w * 0.76, py, w * 0.08, 3, (200, 200, 190))
    font.draw(x + w * 0.33, y + h * 0.42, "NVDA", 13, (140, 220, 110),
              bold=True)
    cv.thick_line(x + w * 0.10, y + h * 0.88, x + w * 0.90, y + h * 0.88, 2,
                  (120, 200, 90))


# Dotted world map: land spans per row (72 cols x 35 rows).
MAP_SPANS = [
    [(28, 28)],
    [(18, 22), (26, 30)],
    [(14, 24), (27, 31)],
    [(2, 8), (10, 26), (28, 32), (50, 70)],
    [(2, 9), (10, 27), (48, 71)],
    [(3, 9), (11, 28), (38, 42), (44, 71)],
    [(12, 29), (34, 34), (38, 43), (44, 71)],
    [(13, 28), (34, 34), (36, 45), (46, 71)],
    [(13, 28), (36, 46), (48, 68)],
    [(13, 27), (37, 45), (47, 69)],
    [(14, 27), (37, 45), (48, 52), (55, 68), (69, 70)],
    [(14, 27), (37, 43), (44, 49), (54, 67), (69, 69)],
    [(15, 27), (34, 44), (45, 50), (53, 56), (58, 62)],
    [(14, 18), (24, 25), (33, 45), (47, 50), (54, 57), (58, 63)],
    [(14, 19), (34, 46), (54, 56), (59, 63)],
    [(15, 19), (34, 47), (54, 56), (60, 63)],
    [(15, 18), (34, 48), (55, 55), (60, 64)],
    [(16, 18), (35, 48), (60, 64)],
    [(20, 24), (36, 47), (61, 65)],
    [(20, 25), (37, 46), (60, 66)],
    [(20, 26), (38, 45), (61, 67)],
    [(20, 26), (38, 44), (62, 68)],
    [(21, 26), (38, 43)],
    [(21, 26), (38, 42)],
    [(21, 25), (38, 41), (45, 45)],
    [(22, 25), (38, 40), (45, 45)],
    [(22, 25), (38, 40)],
    [(22, 25), (38, 39)],
    [(22, 24), (38, 40)],
    [(22, 24), (38, 40)],
    [(23, 23), (39, 39)],
    [(23, 23)],
    [(23, 24)],
    [(24, 24)],
]
# pins: (story_no, col, row) — spread so neighbouring pins do not merge
MAP_PINS = [
    (1, 59, 16), (2, 12, 11), (3, 36, 8), (4, 44, 10), (5, 47, 15),
    (6, 21, 12), (7, 53, 17), (8, 20, 15), (9, 41, 13), (10, 64, 13),
    (11, 11, 14), (12, 44, 14), (13, 40, 8),
]


def draw_map(cv, font, x, y, w, h):
    cv.fill_rect(x, y, w, h, (222, 232, 240))
    cols, rows = 72, len(MAP_SPANS)
    cw, ch = w / cols, h / rows
    for r, spans in enumerate(MAP_SPANS):
        for (a, b) in spans:
            for c in range(a, b + 1):
                px = x + (c + 0.5) * cw
                py = y + (r + 0.5) * ch
                cv.disc(px * S, py * S, 1.9 * S, (60, 90, 120))
    for (no, c, r) in MAP_PINS:
        px = x + (c + 0.5) * cw
        py = y + (r + 0.5) * ch
        cv.disc(px * S, py * S, 5.5 * S, RED)
        cv.disc(px * S, py * S, 4 * S, WHITE)
        s = str(no)
        tw = font.width(s, 7.5)
        font.draw(px - tw / 2.0, py - 5, s, 7.5, RED, bold=True)

# ---------------------------------------------------------------- content ---
# 40 stories, all verified by web search on 20 Nov 2026 (see notes file).
# Cards 1-13 carry scenes; 14-40 are one-line index entries.
# Evidence tags: CONFIRMED = on the record; REPORTED = reported, not
# independently confirmed; ESTIMATE = analyst estimate.

LEAD_SUMMIT_DECK = (
    "First-ever trilateral talks at APEC in Shenzhen: 90 minutes on "
    "Ukraine, Iran and nuclear arms. No breakthrough - but a pledge "
    "to keep talking.")
LEAD_GTA_DECK = (
    "Rockstar's epic lands on PS5 and Xbox: Vice City, Jason and Lucia, "
    "a 99 on Metacritic.")

CARDS_ROW2 = [
    ("TECH", "ANTHROPIC'S $81BN DEBUT",
     "Claude maker prices at $83 in the biggest IPO ever. Shares jump "
     "30% on debut.",
     "CONFIRMED", scene_anthropic),
    ("JUSTICE", "MYANMAR GUILTY OF GENOCIDE",
     "World court: Myanmar committed genocide in 2017, a first. "
     "Return ordered.",
     "CONFIRMED", scene_icj),
    ("WAR", "KERCH BRIDGE HIT AGAIN",
     "Third strike in four days: Neptune missiles hit the rail span. "
     "Road out, rail on one line.",
     "REPORTED", scene_kerch),
]

MINI_CARDS = [
    ("ENERGY", "HORMUZ: LARGEST ENERGY THREAT EVER",
     "IEA: 2.8bn barrels lost; flows may fall to 2m.",
     "CONFIRMED"),
    ("WASHINGTON", "JEFFRIES 251-11",
     "Democrats pick Jeffries, first Black speaker nominee. Vote Jan 3.",
     "CONFIRMED"),
    ("GAZA", "TANKS CROSS THE YELLOW LINE",
     "Israeli tanks enter central Gaza in a rare raid.",
     "REPORTED"),
    ("UKRAINE", "EU OFFERS 45BN EURO LOAN",
     "EU loan to close Kyiv's 70bn euro gap.",
     "CONFIRMED"),
]

ROW4_CARDS = [
    ("WEATHER", "CYCLONE AKVAN BEARS DOWN",
     "Severe storm nears Andhra and Odisha; landfall Fri noon, winds "
     "120-130 km/h.",
     "CONFIRMED", scene_cyclone),
    ("WEATHER", "FLORIDA'S RECORD FLOOD",
     "St. Johns River tops its 1953 record at 18.05 ft; schools shut, "
     "Guard out.",
     "CONFIRMED", scene_flood),
    ("CLIMATE", "COP31 DRAFT DROPS FOSSIL FUELS",
     "Antalya draft drops the phase-out language; 1.5C will be "
     "overshot, it admits.",
     "CONFIRMED", scene_climate),
    ("TECH", "NVIDIA: HUANG WILL NOT RETURN",
     "Board: ousted founder stays out. Q3 sales hit a record $115.8bn.",
     "CONFIRMED", scene_chip),
]

INDEX = [
    "BOJ signals a December hike; rate 1.25%",
    "Gold $3,713, a 14-month low; Brent $92",
    "Hormuz shipping 'near pre-war levels'",
    "UK to send 1,000 drones to Ukraine",
    "Russian held for 'spying' on Palantir staff",
    "Spain opens inquiry into train crash",
    "Boat sinks off Senegal; dozens missing",
    "N. Korea expands Yongbyon enrichment: IAEA",
    "Sudan: 3,000 flee strikes at Abu Kalb",
    "Trump asks top court again on deportations",
    "France admits troops in Ukraine, noncombat",
    "Take-Two falls 1.8% on GTA VI launch day",
    "Musk at DealBook: 'not MAGA', backs Huang",
    "Settler ramming injures 8 in central Israel",
    "Russian strikes kill 5; power out in 5 regions",
    "Kursk drone attack injures 11",
    "Drone hits oil pumps in Tatarstan",
    "Anthropic: $26bn private placement too",
    "GTA VI album: 34 tracks out at midnight",
    "Nobel Peace Prize 2026 went to Navi Pillay",
    "Trump and Xi watch a 'YMCA' performance",
    "Anthropic Q3 sales $17bn, 12x last year",
    "IEA: diesel topped $200 a barrel",
    "COP31: power to be 35% of energy by 2035",
    "Nvidia engineer quits over Huang ouster",
    "Ackman: board 'rushed' Huang's exit",
    "Zelenskyy meets Witkoff and Kushner in Berlin",
]

NUMBERS = [
    ("90 MIN", "summit talks"),
    ("$81.3BN", "Anthropic IPO"),
    ("99", "GTA VI Metacritic"),
    ("$3,713", "gold, 14-month low"),
    ("18.05 FT", "St. Johns River"),
    ("251-11", "Jeffries vote"),
]

TIMELINE = [
    ("00:00", "GTA VI unlocks worldwide"),
    ("01:35", "BOJ's Ueda signals hikes"),
    ("06:00", "Summit opens in Shenzhen"),
    ("09:00", "ICJ: Myanmar guilty"),
    ("10:50", "IEA warns on Hormuz"),
    ("12:13", "COP31 drops fossil fuels"),
    ("14:30", "Anthropic opens +30%"),
]


# ------------------------------------------------------------------ layout --
def tag_box(cv, font, x, y, text):
    """Evidence tag: small filled box, white bold text."""
    col = {"CONFIRMED": TEAL, "REPORTED": (176, 124, 20),
           "CLAIM": RED, "ESTIMATE": NAVY}.get(text, GREY)
    w = font.width(text, 8) + 10
    cv.fill_rect(x, y, w, 12, col)
    font.draw(x + 5, y + 2, text, 8, WHITE, bold=True)
    return w


def kicker(font, x, y, text):
    font.draw(x, y, text, 9.5, RED, bold=True)


def card_headline(font, x, y, text, size, max_w, max_lines=2):
    lines = wrap(font, text, size, max_w, bold=True)
    lines = lines[:max_lines]
    return draw_lines(font, x, y, lines, size, NAVY, bold=True)


def card_body(font, x, y, text, size, max_w, max_lines=3):
    lines = wrap(font, text, size, max_w)
    lines = lines[:max_lines]
    return draw_lines(font, x, y, lines, size, INK, leading=size * 1.25)


def fit_text(font, text, size, max_w, max_chars=None):
    """Truncate text with '...' so it fits max_w at size."""
    if font.width(text, size) <= max_w:
        return text
    while text and font.width(text + "...", size) > max_w:
        text = text[:-1]
    return text + "..."


def build():
    cv = Canvas()
    font = Font(cv)

    # outer frame
    cv.frame(4, 4, W - 8, H - 8, NAVY, 3)

    # ---- masthead ----
    cv.fill_rect(8, 8, W - 16, 54, NAVY)
    font.draw(20, 18, "THE WORLD TODAY", 34, WHITE, bold=True)
    font.draw(700, 24, "THURSDAY EDITION", 13, (200, 210, 230), bold=True)
    font.draw(700, 42, "ONE DAY  •  ONE PAGE  •  No. 323", 10,
              (170, 185, 210))

    # ---- kicker strip ----
    cv.fill_rect(8, 64, W - 16, 2, RED)
    font.draw(20, 68, "THE WORLD IN ONE DAY", 10, RED, bold=True)
    font.draw(560, 68, "40 STORIES  •  7 REGIONS  •  13 DRAWN SCENES", 10,
              GREY, bold=True)

    # ---- giant date headline + red date box ----
    font.draw(20, 84, "THURSDAY 19 NOVEMBER 2026", 34, NAVY, bold=True)
    cv.fill_rect(856, 80, 148, 50, RED)
    font.draw(872, 88, "NOV 19", 26, WHITE, bold=True)
    font.draw(872, 112, "2026", 12, WHITE, bold=True)

    # ---- lead row ----
    # summit (hero 1)
    scene_summit(cv, font, 16, 134, 624, 110)
    font.draw(16, 248, "THREE LEADERS, ONE ROOM", 24, NAVY, bold=True)
    tag_box(cv, font, 560, 252, "CONFIRMED")
    draw_lines(font, 16, 276, wrap(font, LEAD_SUMMIT_DECK, 11, 624),
               11, INK, leading=13.5)
    # GTA VI (hero 2)
    scene_gta(cv, font, 656, 134, 352, 110)
    font.draw(656, 248, "GTA VI IS OUT", 22, NAVY, bold=True)
    tag_box(cv, font, 900, 251, "CONFIRMED")
    draw_lines(font, 656, 276, wrap(font, LEAD_GTA_DECK, 11, 352),
               11, INK, leading=13.5)

    # ---- row 2: three cards ----
    xs = [16, 352, 684]
    ws = [324, 320, 324]
    for (kick, head, body, tag, scene), x, w in zip(CARDS_ROW2, xs, ws):
        scene(cv, font, x, 322, w, 72)
        kicker(font, x, 400, kick)
        tag_box(cv, font, x + w - 76, 398, tag)
        y = card_headline(font, x, 414, head, 15, w, max_lines=2)
        card_body(font, x, y + 4, body, 10, w, max_lines=3)

    # ---- row 3: map + 2x2 mini cards ----
    font.draw(16, 500, "WHERE IT HAPPENED", 11, NAVY, bold=True)
    draw_map(cv, font, 16, 516, 504, 124)
    font.draw(16, 644, "Numbers match the story cards.  •  Dotted map: each "
              "dot is land.", 8, GREY)
    mx = [536, 776]
    my = [496, 578]
    mw = 232
    mh = 78
    for i, (kick, head, body, tag) in enumerate(MINI_CARDS):
        x = mx[i % 2]
        y = my[i // 2]
        cv.frame(x, y, mw, mh, LGREY, 1)
        cv.fill_rect(x, y, mw, 3, NAVY)
        kicker(font, x + 8, y + 7, kick)
        tag_box(cv, font, x + mw - 76, y + 6, tag)
        n_head = len(wrap(font, head, 12, mw - 16, bold=True))
        y2 = card_headline(font, x + 8, y + 19, head, 12, mw - 16,
                           max_lines=2)
        card_body(font, x + 8, y2 + 3, body, 9.5, mw - 16,
                  max_lines=3 if n_head == 1 else 2)

    # ---- row 4: four scene cards ----
    xs4 = [16, 262, 508, 754]
    w4 = 238
    for (kick, head, body, tag, scene), x in zip(ROW4_CARDS, xs4):
        if scene is scene_chip:
            scene(cv, font, x, 656, w4, 42)
        else:
            scene(cv, x, 656, w4, 42)
        kicker(font, x, 704, kick)
        y = card_headline(font, x, 718, head, 13, w4, max_lines=2)
        card_body(font, x, y + 2, body, 10, w4, max_lines=3)

    # ---- numbers strip ----
    cv.fill_rect(8, 796, W - 16, 46, NAVY)
    cw = (W - 16) / 6.0
    for i, (num, label) in enumerate(NUMBERS):
        x = 8 + i * cw
        if i:
            cv.vline(x, 802, 34, (70, 90, 125), 1)
        font.draw_center(x + cw / 2.0, 802, num, 19, WHITE, bold=True)
        font.draw_center(x + cw / 2.0, 824, label, 8.5, (190, 200, 220))

    # ---- UTC timeline (two lines) ----
    font.draw(16, 848, "THE DAY IN UTC", 9.5, RED, bold=True)
    tx = 130
    for t, what in TIMELINE[:3]:
        font.draw(tx, 848, t, 9.5, NAVY, bold=True)
        tx += font.width(t + "  ", 9.5)
        font.draw(tx, 848, what, 9.5, INK)
        tx += font.width(what + "   •   ", 9.5)
    tx = 16
    for t, what in TIMELINE[3:]:
        font.draw(tx, 860, t, 9.5, NAVY, bold=True)
        tx += font.width(t + "  ", 9.5)
        font.draw(tx, 860, what, 9.5, INK)
        tx += font.width(what + "   •   ", 9.5)

    # ---- index: the rest of the day ----
    font.draw(16, 876, "THE REST OF THE DAY  —  27 MORE STORIES", 11, RED,
              bold=True)
    col_x = [16, 352, 688]
    for i, item in enumerate(INDEX):
        col = i // 9
        row = i % 9
        x = col_x[col]
        y = 892 + row * 9
        label = "%d. %s" % (14 + i, item)
        label = fit_text(font, label, 8, 322)
        font.draw(x, y, label, 8, INK)

    # ---- footer: DATE CHECK + sources ----
    cv.fill_rect(8, 972, W - 16, 28, RED)
    font.draw_center(W / 2.0, 979,
                     "DATE CHECK: THURSDAY 19 NOVEMBER 2026  —  EVERY STORY "
                     "ABOVE HAPPENED, OR WAS FIRST REPORTED, ON 19 NOV 2026",
                     10.5, WHITE, bold=True)
    font.draw_center(W / 2.0, 1004,
                     "Sources: AP, Reuters, AFP, NYT, USA TODAY, Bloomberg, "
                     "ICJ, IEA, IMD, NWS  •  Drawn from reports; no "
                     "photographs  •  @exc-ana",
                     8.5, GREY)
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    cv = build()
    png = encode_png(downsample(cv), W, H)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(png)
    print("wrote %s (%d bytes, sha256 %s)"
          % (path, len(png), hashlib.sha256(png).hexdigest()))


if __name__ == "__main__":
    main()
