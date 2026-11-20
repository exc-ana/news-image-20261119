#!/usr/bin/env python3
"""THE WORLD TODAY - Thursday 19 November 2026.

A one-page newspaper broadsheet that sums up the world's news of
Thursday 19 November 2026. Written from scratch in this session:
own rasterizer, own vector stroke font, own PNG encoder, pure
Python 3.13 standard library, no network, deterministic.

Pipeline: draw everything on a 2048x2048 canvas (2x supersampling),
box-average downsample to 1024x1024, encode PNG, write to
$MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).
"""

import math
import os
import struct
import zlib

W = 2048
H = 2048

# ---------------------------------------------------------------- palette
NAVY = (13, 27, 62)
NAVY_DK = (8, 18, 44)
NAVY_LT = (38, 58, 110)
RED = (198, 32, 32)
RED_DK = (160, 22, 22)
PAPER = (247, 243, 232)
PAPER_DK = (238, 232, 214)
INK = (18, 22, 34)
GREY = (96, 100, 112)
GREY_LT = (178, 182, 190)
GOLD = (214, 164, 48)
GOLD_LT = (240, 205, 110)
GREEN = (28, 110, 68)
GREEN_DK = (16, 74, 44)
TEAL = (24, 120, 128)
BLUE = (36, 92, 168)
SKY = (168, 200, 228)
SKY_DK = (120, 160, 205)
SAND = (226, 205, 160)
WHITE = (255, 255, 255)
CREAM = (244, 236, 214)
ORANGE = (232, 110, 42)
DUSK1 = (242, 165, 65)
DUSK2 = (198, 91, 124)
DUSK3 = (46, 42, 92)
SUNSET1 = (122, 62, 140)
SUNSET2 = (214, 84, 120)
SUNSET3 = (242, 140, 70)

# ---------------------------------------------------------------- canvas
class Canvas:
    """RGB bytearray canvas with a clip rectangle."""

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.clip = (0, 0, w, h)

    def set_clip(self, x0, y0, x1, y1):
        self.clip = (max(0, int(x0)), max(0, int(y0)),
                     min(self.w, int(x1)), min(self.h, int(y1)))

    def reset_clip(self):
        self.clip = (0, 0, self.w, self.h)

    def put(self, x, y, c):
        cx0, cy0, cx1, cy1 = self.clip
        if cx0 <= x < cx1 and cy0 <= y < cy1:
            i = (y * self.w + x) * 3
            self.px[i] = c[0]
            self.px[i + 1] = c[1]
            self.px[i + 2] = c[2]

    def _span(self, y, x0, x1, c):
        cx0, cy0, cx1, cy1 = self.clip
        if y < cy0 or y >= cy1:
            return
        x0 = max(x0, cx0)
        x1 = min(x1, cx1 - 1)
        if x1 < x0:
            return
        i = (y * self.w + x0) * 3
        r, g, b = c
        for _ in range(x0, x1 + 1):
            self.px[i] = r
            self.px[i + 1] = g
            self.px[i + 2] = b
            i += 3

    def rect(self, x, y, w, h, c):
        cx0, cy0, cx1, cy1 = self.clip
        x0 = max(int(x), cx0)
        y0 = max(int(y), cy0)
        x1 = min(int(x + w), cx1)
        y1 = min(int(y + h), cy1)
        for yy in range(y0, y1):
            self._span(yy, x0, x1 - 1, c)

    def disc(self, cx, cy, r, c):
        r = int(r)
        if r <= 0:
            return
        for yy in range(max(cy - r, self.clip[1]),
                        min(cy + r + 1, self.clip[3])):
            dy = yy - cy
            dx = int((r * r - dy * dy) ** 0.5)
            self._span(yy, cx - dx, cx + dx, c)

    def ellipse(self, cx, cy, rx, ry, c):
        rx = int(rx)
        ry = int(ry)
        if rx <= 0 or ry <= 0:
            return
        for yy in range(max(cy - ry, self.clip[1]),
                        min(cy + ry + 1, self.clip[3])):
            dy = (yy - cy) / ry
            if abs(dy) > 1:
                continue
            dx = int(rx * math.sqrt(1 - dy * dy))
            self._span(yy, cx - dx, cx + dx, c)

    def poly(self, pts, c):
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        y0 = max(int(math.floor(min(ys))), self.clip[1])
        y1 = min(int(math.ceil(max(ys))), self.clip[3] - 1)
        n = len(pts)
        for y in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                x1, y1p = pts[i]
                x2, y2p = pts[(i + 1) % n]
                if (y1p <= y < y2p) or (y2p <= y < y1p):
                    if y2p != y1p:
                        xs.append(x1 + (y - y1p) * (x2 - x1) / (y2p - y1p))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self._span(y, int(math.ceil(xs[i])),
                           int(math.floor(xs[i + 1])), c)

    def line(self, x1, y1, x2, y2, w, c):
        dx = x2 - x1
        dy = y2 - y1
        L = math.hypot(dx, dy)
        if L < 0.5:
            self.disc(int(round(x1)), int(round(y1)),
                      max(1, int(round(w / 2))), c)
            return
        nx = -dy / L * w / 2.0
        ny = dx / L * w / 2.0
        self.poly([(x1 + nx, y1 + ny), (x2 + nx, y2 + ny),
                   (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)], c)
        r = max(1, int(round(w / 2)))
        self.disc(int(round(x1)), int(round(y1)), r, c)
        self.disc(int(round(x2)), int(round(y2)), r, c)

    def vgrad(self, x, y, w, h, c1, c2):
        for yy in range(int(h)):
            t = yy / max(1, int(h) - 1)
            c = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
            self.rect(x, y + yy, w, 1, c)

    def hgrad(self, x, y, w, h, c1, c2):
        for xx in range(int(w)):
            t = xx / max(1, int(w) - 1)
            c = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
            self.rect(x + xx, y, 1, h, c)

# ---------------------------------------------------------------- stroke font
# Glyphs are polylines on a 10-wide x 14-tall grid (cap top y=0,
# baseline y=14; a few descenders reach y=17). One point = two
# characters: x in 0-9,A (0..10), y in 0-9,A-H (0..17). Strokes are
# separated by ';'. A one-point stroke renders as a dot.
FONT = {
    "A": "0E50;50AE;2878",
    "B": "000E;007092957707;0787A9AC8E0E",
    "C": "92501105091D5E9C",
    "D": "000E;0070A3AB7E0E",
    "E": "000E;0080;0777;0E8E",
    "F": "000E;0080;0777",
    "G": "92501105091D5E9C;7999;999E",
    "H": "000E;A00E;07A7",
    "I": "2080;505E;2E8E",
    "J": "4090;909B7E3E",
    "K": "000E;0790;47AE",
    "L": "000E;0EAE",
    "M": "0E00;005A;5AA0;A0AE",
    "N": "0E00;00AE;AEA0",
    "O": "2080A2AC8E2E0C0220",
    "P": "000E;007092957707",
    "Q": "2080A2AC8E2E0C0220;79AE",
    "R": "000E;007092957707;47AE",
    "S": "91602104174788AA9D6E2E0D",
    "T": "00A0;505E",
    "U": "000C;0C2E8EAC;A0AC",
    "V": "005E;5EA0",
    "W": "002E;2E55;558E;8EA0",
    "X": "00AE;A00E",
    "Y": "0057;57A0;575E",
    "Z": "00A0;A00E;0EAE",
    "0": "2080A2AC8E2E0C0220",
    "1": "2350;505E;2E8E",
    "2": "11408194783B0E9E",
    "3": "115092957747;4787AA9D5E1D",
    "4": "7009;0999;705E",
    "5": "0090;0007;0777AA9D5E2D",
    "6": "915012061B4E8DAA875729",
    "7": "00A0;903E",
    "8": "21719386572613;28789A8D5E2D1A",
    "9": "22719387582704;937E",
    ".": "5D",
    ",": "5D;5D4F3H",
    ":": "54;5B",
    ";": "54;5D4F3H",
    "!": "505B;5D",
    "?": "1150929577575B;5D",
    "'": "6044",
    '"': "2013;7063",
    "-": "1797",
    "\u2014": "07A7",
    "\u2022": "57",
    "/": "802E",
    "%": "802E;22332413;8A9B8C7B",
    "(": "70303B7E",
    ")": "30737B3E",
    "$": "91602104174788AA9D6E2E0D;505E",
    "+": "1797;525C",
    "=": "1595;1999",
    " ": "",
}
# Narrow / wide advance overrides (default advance is 11 grid units).
ADV = {"I": 6, "J": 8, "L": 8, "T": 10, "F": 9, "1": 7, ".": 5, ",": 5,
       ":": 5, ";": 5, "!": 5, "'": 4, '"': 7, "-": 7, "\u2014": 11,
       "\u2022": 6, "/": 7, "%": 13, "(": 6, ")": 6, "$": 11, "+": 10,
       "=": 10, " ": 6}


def _v(ch):
    o = ord(ch)
    if 48 <= o <= 57:
        return o - 48
    return o - 55  # 'A' -> 10 ... 'H' -> 17


def _parse_glyph(s):
    strokes = []
    for part in s.split(";"):
        pts = []
        for i in range(0, len(part), 2):
            pts.append((_v(part[i]), _v(part[i + 1])))
        strokes.append(pts)
    return strokes


FONT_P = {ch: _parse_glyph(s) for ch, s in FONT.items()}


def text_w(s, size, cw=1.0, spacing=0.0):
    """Width of s in working pixels at cap-height `size`."""
    sc = size / 14.0
    w = 0.0
    for ch in s:
        w += ADV.get(ch, 11) * sc * cw + spacing
    return w - spacing if s else 0.0


def draw_text(cv, x, y, s, size, color, weight=1.0, cw=1.0, slant=0.0,
              spacing=0.0, align="l"):
    """Draw s with cap-top at y. weight scales stroke thickness."""
    sc = size / 14.0
    wdt = max(2.0, size * 0.11 * weight)
    tw = text_w(s, size, cw, spacing)
    if align == "c":
        x -= tw / 2.0
    elif align == "r":
        x -= tw
    cx = x
    for ch in s:
        if ch == " ":
            cx += ADV.get(ch, 11) * sc * cw + spacing
            continue
        gl = FONT_P.get(ch)
        if gl is None:
            cx += 11 * sc * cw + spacing
            continue
        for stroke in gl:
            pts = []
            for (px, py) in stroke:
                gx = cx + px * sc * cw + slant * (size - py * sc)
                gy = y + py * sc
                pts.append((gx, gy))
            if len(pts) == 1:
                cv.disc(int(round(pts[0][0])), int(round(pts[0][1])),
                        max(1, int(round(wdt / 2))), color)
            else:
                for i in range(len(pts) - 1):
                    cv.line(pts[i][0], pts[i][1], pts[i + 1][0],
                            pts[i + 1][1], wdt, color)
        cx += ADV.get(ch, 11) * sc * cw + spacing


def wrap(s, size, maxw, cw=1.0, spacing=0.0):
    """Greedy word wrap; returns a list of lines."""
    words = s.split(" ")
    lines = []
    cur = ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if text_w(trial, size, cw, spacing) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def draw_para(cv, x, y, lines, size, lh, color, weight=1.0, cw=1.0,
              spacing=0.0):
    for i, ln in enumerate(lines):
        draw_text(cv, x, y + i * lh, ln, size, color, weight=weight,
                  cw=cw, spacing=spacing)

# ---------------------------------------------------------------- png output
def downsample(cv):
    """Box-average 2048x2048 -> 1024x1024 RGB bytes."""
    out = bytearray(1024 * 1024 * 3)
    src = cv.px
    W = cv.w
    for y in range(1024):
        for x in range(1024):
            r = g = b = 0
            for dy in range(2):
                base = ((2 * y + dy) * W + 2 * x) * 3
                for dx in range(2):
                    i = base + dx * 3
                    r += src[i]
                    g += src[i + 1]
                    b += src[i + 2]
            o = (y * 1024 + x) * 3
            out[o] = r // 4
            out[o + 1] = g // 4
            out[o + 2] = b // 4
    return out


def png_bytes(rgb, w, h):
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        row = rgb[y * stride:(y + 1) * stride]
        raw.append(1)  # Sub filter
        raw.extend(row[0:3])
        for i in range(3, stride):
            raw.append((row[i] - row[i - 3]) & 0xFF)
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        c += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
        return c

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", comp) + chunk(b"IEND", b""))


# ---------------------------------------------------------------- small parts
def tag(cv, x, y, s, color, size=17):
    """Small filled tag with white text, e.g. CONFIRMED / REPORTED."""
    w = int(text_w(s, size, cw=0.92) + 16)
    cv.rect(x, y, w, size + 8, color)
    draw_text(cv, x + 8, y + 4, s, size, WHITE, weight=1.2, cw=0.92)
    return w


def hrule(cv, x, y, w, color, t=2):
    cv.rect(x, y, w, t, color)


def card_frame(cv, x, y, w, h):
    cv.rect(x, y, w, h, PAPER)
    cv.rect(x, y, w, 2, INK)
    cv.rect(x, y + h - 2, w, 2, INK)
    cv.rect(x, y, 2, h, INK)
    cv.rect(x + w - 2, y, 2, h, INK)

# ---------------------------------------------------------------- scenes
# Every scene draws inside its own panel (x, y, w, h) in working
# pixels, clipped to the panel. All radii are based on the panel
# height so nothing bleeds into neighbouring cards.

def _det(i, m):
    """Deterministic pseudo-random integer in [0, m) from index i."""
    return ((i * 2654435761 + 97) % 1000) * m // 1000


def scene_summit(cv, x, y, w, h):
    cv.set_clip(x, y, x + w, y + h)
    cv.vgrad(x, y, w, int(h * 0.55), DUSK1, DUSK2)
    cv.vgrad(x, y + int(h * 0.55), w, h - int(h * 0.55), DUSK2, DUSK3)
    # low sun
    cv.disc(x + int(w * 0.72), y + int(h * 0.42), int(h * 0.20),
            (250, 214, 140))
    # skyline silhouettes
    base = y + int(h * 0.72)
    bx = x
    i = 0
    while bx < x + w:
        bw = int(w * 0.045) + _det(i, int(w * 0.05))
        bh = int(h * 0.16) + _det(i + 40, int(h * 0.22))
        cv.rect(bx, base - bh, bw, bh + int(h * 0.28), NAVY_DK)
        for wy in range(3):
            for wx in range(2):
                if _det(i * 7 + wy * 3 + wx, 3) == 0:
                    cv.rect(bx + 6 + wx * (bw // 2), base - bh + 8 + wy * 14,
                            5, 7, GOLD_LT)
        bx += bw + 4
        i += 1
    # red carpet + long table (shorter, so the figures read)
    cv.rect(x, y + int(h * 0.80), w, int(h * 0.20), RED_DK)
    cv.rect(x, y + int(h * 0.66), w, int(h * 0.12), (178, 28, 28))
    cv.rect(x, y + int(h * 0.66), w, 4, (232, 120, 110))
    # three flags behind the table: China, Russia, USA
    for j, fx in enumerate([0.30, 0.50, 0.70]):
        px = x + int(w * fx)
        cv.rect(px, y + int(h * 0.28), 3, int(h * 0.38), (220, 220, 210))
        fw, fh = int(w * 0.09), int(h * 0.15)
        fy = y + int(h * 0.28)
        if j == 0:
            cv.rect(px + 3, fy, fw, fh, RED)
            cv.disc(px + 3 + fw // 3, fy + fh // 3, 6, GOLD_LT)
        elif j == 1:
            cv.rect(px + 3, fy, fw, fh, WHITE)
            cv.rect(px + 3, fy + fh // 3, fw, fh // 3, BLUE)
            cv.rect(px + 3, fy + 2 * fh // 3, fw, fh // 3, RED)
        else:
            for s in range(4):
                cv.rect(px + 3, fy + s * (fh // 4), fw,
                        fh // 4 - 1, RED if s % 2 == 0 else WHITE)
            cv.rect(px + 3, fy, fw // 2, fh // 2, NAVY)
        # seated figure: head + shoulders
        hx = px + 3 + fw // 2
        cv.disc(hx, y + int(h * 0.58), int(h * 0.06), (232, 196, 160))
        cv.ellipse(hx, y + int(h * 0.68), int(w * 0.042), int(h * 0.055),
                   NAVY_DK if j != 1 else (40, 44, 60))
    cv.reset_clip()


def scene_gta(cv, x, y, w, h):
    cv.set_clip(x, y, x + w, y + h)
    cv.vgrad(x, y, w, int(h * 0.5), SUNSET1, SUNSET2)
    cv.vgrad(x, y + int(h * 0.5), w, h - int(h * 0.5), SUNSET2, SUNSET3)
    # big sun
    cv.disc(x + int(w * 0.68), y + int(h * 0.34), int(h * 0.26),
            (252, 222, 150))
    cv.disc(x + int(w * 0.68), y + int(h * 0.34), int(h * 0.19),
            (255, 240, 190))
    # skyline
    base = y + int(h * 0.78)
    bx = x + 6
    i = 0
    while bx < x + w - 10:
        bw = int(w * 0.06) + _det(i, int(w * 0.05))
        bh = int(h * 0.14) + _det(i + 21, int(h * 0.20))
        cv.rect(bx, base - bh, bw, bh + int(h * 0.22), (24, 14, 44))
        for wy in range(2):
            if _det(i * 5 + wy, 2) == 0:
                cv.rect(bx + 5, base - bh + 8 + wy * 14, 5, 6,
                        (255, 130, 170))
        bx += bw + 5
        i += 1
    # palms
    for px, ph in [(0.12, 0.30), (0.88, 0.26)]:
        tx = x + int(w * px)
        ty = y + int(h * 0.78)
        cv.line(tx, ty, tx + 6, ty - int(h * ph), 5, (16, 30, 20))
        for a in range(-2, 3):
            cv.line(tx + 6, ty - int(h * ph),
                    tx + 6 + a * 16, ty - int(h * ph) + 10 + abs(a) * 6,
                    3, (20, 90, 50))
    # car silhouette (scaled to the panel, not absolute offsets)
    cw_ = int(w * 0.30)
    cx0 = x + int(w * 0.32)
    cy0 = y + int(h * 0.84)
    cv.rect(cx0, cy0, cw_, int(h * 0.08), (12, 10, 26))
    cv.poly([(cx0 + int(cw_ * 0.05), cy0),
             (cx0 + int(cw_ * 0.16), cy0 - int(h * 0.07)),
             (cx0 + int(cw_ * 0.42), cy0 - int(h * 0.07)),
             (cx0 + int(cw_ * 0.95), cy0)], (12, 10, 26))
    cv.disc(cx0 + int(cw_ * 0.14), cy0 + int(h * 0.08), 7, (5, 5, 10))
    cv.disc(cx0 + int(cw_ * 0.86), cy0 + int(h * 0.08), 7, (5, 5, 10))
    # big VI letters
    draw_text(cv, x + 14, y + 8, "VI", int(h * 0.42), GOLD_LT,
              weight=2.0, cw=1.05)
    cv.reset_clip()


def scene_chart(cv, x, y, w, h):
    cv.set_clip(x, y, x + w, y + h)
    cv.rect(x, y, w, h, (240, 244, 248))
    base = y + h - int(h * 0.22)
    # gridlines
    for g in range(3):
        gy = y + int(h * 0.18) + g * int(h * 0.22)
        cv.rect(x + 8, gy, w - 16, 2, (210, 216, 224))
    bw = int(w * 0.24)
    # SpaceX bar $90.0bn
    b1x = x + int(w * 0.14)
    b1h = int(h * 0.52)
    cv.rect(b1x, base - b1h, bw, b1h, (120, 128, 140))
    # Anthropic bar $81.3bn
    b2x = x + int(w * 0.56)
    b2h = int(h * 0.47)
    cv.rect(b2x, base - b2h, bw, b2h, RED)
    cv.rect(b2x, base - b2h, bw, 5, RED_DK)
    draw_text(cv, b1x + bw // 2, base - b1h - 26, "$90.0BN", 22, INK,
              weight=1.3, cw=0.9, align="c")
    draw_text(cv, b2x + bw // 2, base - b2h - 26, "$81.3BN", 22, RED,
              weight=1.5, cw=0.9, align="c")
    draw_text(cv, b1x + bw // 2, base + 8, "SPACEX", 17, GREY,
              weight=1.2, cw=0.9, align="c")
    draw_text(cv, b2x + bw // 2, base + 8, "ANTHROPIC", 17, RED,
              weight=1.4, cw=0.9, align="c")
    draw_text(cv, b1x + bw // 2, base + 30, "JUN", 15, GREY, cw=0.9,
              align="c")
    draw_text(cv, b2x + bw // 2, base + 30, "NOV 19", 15, RED,
              weight=1.2, cw=0.9, align="c")
    cv.reset_clip()


def scene_icj(cv, x, y, w, h):
    cv.set_clip(x, y, x + w, y + h)
    cv.vgrad(x, y, w, h, (206, 224, 238), (238, 240, 234))
    # lawn
    cv.rect(x, y + int(h * 0.82), w, int(h * 0.18), (96, 140, 80))
    # Peace Palace facade
    bx = x + int(w * 0.14)
    bw = int(w * 0.72)
    by = y + int(h * 0.30)
    bh = int(h * 0.52)
    cv.rect(bx, by, bw, bh, (236, 228, 204))
    cv.rect(bx - 8, by - 6, bw + 16, 10, (210, 200, 170))
    # pediment
    cv.poly([(bx + bw // 2 - int(w * 0.10), by - 6),
             (bx + bw // 2 + int(w * 0.10), by - 6),
             (bx + bw // 2, by - int(h * 0.16))], (226, 216, 186))
    # dome
    cv.ellipse(bx + bw // 2, by - 4, int(w * 0.05), int(h * 0.09),
               (120, 140, 120))
    # columns
    for i in range(6):
        cxp = bx + 14 + i * ((bw - 28) // 5)
        cv.rect(cxp, by + 10, 8, bh - 20, (214, 204, 176))
    # door + flag
    cv.rect(bx + bw // 2 - 14, by + bh - int(h * 0.16), 28,
            int(h * 0.16), (90, 70, 50))
    cv.rect(bx + bw // 2 - 1, by - int(h * 0.24), 3, int(h * 0.24), INK)
    cv.rect(bx + bw // 2 + 2, by - int(h * 0.24), 26, 14, BLUE)
    cv.reset_clip()


def scene_kerch(cv, x, y, w, h):
    cv.set_clip(x, y, x + w, y + h)
    cv.vgrad(x, y, w, int(h * 0.62), (170, 190, 208), (140, 165, 190))
    # sea
    cv.vgrad(x, y + int(h * 0.62), w, h - int(h * 0.62),
             (44, 96, 150), (26, 66, 118))
    for i in range(14):
        wx = x + _det(i, w)
        wy = y + int(h * 0.66) + _det(i + 9, int(h * 0.28))
        cv.rect(wx, wy, 26, 3, (150, 190, 220))
    # bridge deck + arch
    dy = y + int(h * 0.52)
    cv.rect(x, dy, w, 7, (200, 204, 210))
    cv.line(x + int(w * 0.10), dy, x + int(w * 0.42), dy - int(h * 0.30),
            6, (180, 184, 192))
    cv.line(x + int(w * 0.42), dy - int(h * 0.30),
            x + int(w * 0.74), dy, 6, (180, 184, 192))
    # collapsed span, tilted into the water
    cv.line(x + int(w * 0.74), dy, x + int(w * 0.86),
            dy + int(h * 0.22), 7, (150, 154, 162))
    # explosion flash + smoke
    fx, fy = x + int(w * 0.58), dy - int(h * 0.10)
    cv.disc(fx, fy, int(h * 0.10), (255, 190, 80))
    cv.disc(fx, fy, int(h * 0.06), (255, 240, 170))
    for sx, sy, sr in [(0.50, 0.24, 10), (0.56, 0.18, 13), (0.63, 0.22, 9)]:
        cv.disc(x + int(w * sx), y + int(h * sy), sr, (110, 112, 118))
    cv.reset_clip()

def scene_gulf(cv, x, y, w, h):
    """Zoomed Strait of Hormuz inset: sea, land, tanker route."""
    cv.set_clip(x, y, x + w, y + h)
    cv.rect(x, y, w, h, (178, 212, 232))
    # land: Iran (top) and Arabia (bottom)
    cv.poly([(x, y), (x + w, y), (x + w, y + int(h * 0.30)),
             (x + int(w * 0.55), y + int(h * 0.38)),
             (x + int(w * 0.30), y + int(h * 0.22)), (x, y + int(h * 0.26))],
            SAND)
    cv.poly([(x, y + h), (x + w, y + h), (x + w, y + int(h * 0.72)),
             (x + int(w * 0.62), y + int(h * 0.62)),
             (x + int(w * 0.30), y + int(h * 0.80)), (x, y + int(h * 0.74))],
            SAND)
    draw_text(cv, x + 10, y + 8, "IRAN", 15, (120, 100, 70),
              weight=1.2, cw=0.9)
    draw_text(cv, x + w - 10, y + h - 24, "ARABIA", 15, (120, 100, 70),
              weight=1.2, cw=0.9, align="r")
    # tanker route: dashed red line through the strait
    for i in range(9):
        t = i / 8.0
        rx = x + int(w * (0.06 + 0.88 * t))
        ry = y + int(h * (0.52 - 0.10 * math.sin(t * math.pi)))
        cv.disc(rx, ry, 4, RED)
    # two tankers
    for tx, ty in [(0.30, 0.52), (0.68, 0.46)]:
        txp = x + int(w * tx)
        typ = y + int(h * ty)
        cv.rect(txp - 16, typ - 4, 32, 9, (30, 30, 40))
        cv.rect(txp + 2, typ - 10, 8, 6, (30, 30, 40))
    draw_text(cv, x + w // 2, y + int(h * 0.58), "HORMUZ", 17, RED_DK,
              weight=1.5, cw=0.9, align="c")
    cv.reset_clip()


def scene_capitol(cv, x, y, w, h):
    cv.set_clip(x, y, x + w, y + h)
    cv.vgrad(x, y, w, h, (208, 224, 238), (240, 238, 230))
    cv.rect(x, y + int(h * 0.84), w, int(h * 0.16), (100, 140, 90))
    cx = x + w // 2
    base = y + int(h * 0.84)
    # wings
    cv.rect(x + int(w * 0.08), base - int(h * 0.22), int(w * 0.84),
            int(h * 0.22), (232, 230, 222))
    # dome drum + dome
    cv.rect(cx - int(w * 0.10), base - int(h * 0.42), int(w * 0.20),
            int(h * 0.22), (222, 220, 210))
    cv.ellipse(cx, base - int(h * 0.42), int(w * 0.13), int(h * 0.20),
               (200, 198, 188))
    cv.rect(cx - 1, base - int(h * 0.66), 3, int(h * 0.10), INK)
    cv.rect(cx + 2, base - int(h * 0.66), 18, 10, (180, 40, 40))
    # columns
    for i in range(5):
        cv.rect(cx - int(w * 0.16) + i * int(w * 0.08),
                base - int(h * 0.20), 6, int(h * 0.20), (200, 196, 184))
    cv.reset_clip()


def scene_gaza(cv, x, y, w, h):
    cv.set_clip(x, y, x + w, y + h)
    cv.vgrad(x, y, w, h, (238, 220, 180), (214, 186, 138))
    # yellow ceasefire line
    ly = y + int(h * 0.62)
    for i in range(10):
        cv.rect(x + i * (w // 10), ly, w // 20, 4, GOLD)
    # two tanks crossing it
    for tx in [0.22, 0.58]:
        txp = x + int(w * tx)
        typ = ly - int(h * 0.10)
        cv.rect(txp, typ, int(w * 0.24), int(h * 0.13), (52, 66, 44))
        cv.rect(txp + 8, typ - int(h * 0.09), int(w * 0.10),
                int(h * 0.09), (52, 66, 44))
        cv.line(txp + int(w * 0.10), typ - int(h * 0.05),
                txp + int(w * 0.26), typ - int(h * 0.08), 4, (40, 52, 34))
        cv.disc(txp + 10, typ + int(h * 0.13), 6, (30, 34, 28))
        cv.disc(txp + int(w * 0.24) - 10, typ + int(h * 0.13), 6,
                (30, 34, 28))
    # dust puffs
    for sx, sy, sr in [(0.15, 0.30, 10), (0.80, 0.34, 12), (0.45, 0.24, 8)]:
        cv.disc(x + int(w * sx), y + int(h * sy), sr, (226, 208, 172))
    cv.reset_clip()


def scene_eu(cv, x, y, w, h):
    cv.set_clip(x, y, x + w, y + h)
    cv.rect(x, y, w, h, (0, 46, 110))
    cx, cy = x + w // 2, y + int(h * 0.42)
    r = int(h * 0.30)
    for i in range(12):
        a = -math.pi / 2 + i * math.pi / 6
        cv.disc(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)),
                max(3, int(h * 0.035)), GOLD)
    draw_text(cv, cx, y + int(h * 0.62), "45BN", int(h * 0.26), GOLD,
              weight=1.6, cw=0.95, align="c")
    cv.reset_clip()


def scene_akvan(cv, x, y, w, h):
    cv.set_clip(x, y, x + w, y + h)
    cv.vgrad(x, y, w, h, NAVY_DK, (30, 60, 110))
    # cyclone spiral: polyline, radius grows with angle
    cx, cy = x + w // 2, y + int(h * 0.46)
    pts = []
    for a in range(0, 1080, 12):
        r = int(h * 0.30) * a / 1080.0
        ang = math.radians(a)
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang) * 0.85))
    for i in range(len(pts) - 1):
        cv.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], 4,
                (220, 228, 240))
    cv.disc(cx, cy, int(h * 0.07), (240, 244, 250))
    # rain streaks
    for i in range(12):
        rx = x + _det(i, w)
        ry = y + _det(i + 30, int(h * 0.7))
        cv.line(rx, ry, rx - 6, ry + 16, 2, (150, 180, 210))
    # coastline at bottom
    cv.rect(x, y + int(h * 0.88), w, int(h * 0.12), (60, 90, 60))
    cv.reset_clip()


def scene_florida(cv, x, y, w, h):
    cv.set_clip(x, y, x + w, y + h)
    cv.vgrad(x, y, w, int(h * 0.55), (150, 170, 190), (190, 200, 205))
    cv.vgrad(x, y + int(h * 0.55), w, h - int(h * 0.55),
             (40, 90, 140), (24, 60, 110))
    for i in range(10):
        wx = x + _det(i, w)
        wy = y + int(h * 0.60) + _det(i + 5, int(h * 0.30))
        cv.rect(wx, wy, 30, 3, (160, 200, 225))
    # half-submerged rooftop + chimney
    rx = x + int(w * 0.18)
    ry = y + int(h * 0.52)
    cv.rect(rx, ry, int(w * 0.55), int(h * 0.14), (70, 60, 52))
    cv.poly([(rx - 8, ry), (rx + int(w * 0.28), ry - int(h * 0.12)),
             (rx + int(w * 0.55) + 8, ry)], (52, 44, 40))
    cv.rect(rx + int(w * 0.44), ry - int(h * 0.20), 10, int(h * 0.20),
            (90, 70, 60))
    # gauge post
    gx = x + int(w * 0.84)
    cv.rect(gx, y + int(h * 0.30), 4, int(h * 0.55), WHITE)
    cv.rect(gx - 6, y + int(h * 0.30), 16, 4, RED)
    draw_text(cv, gx - 8, y + int(h * 0.16), "18.95", 15, WHITE,
              weight=1.3, cw=0.85, align="r")
    cv.reset_clip()


def scene_cop31(cv, x, y, w, h):
    cv.set_clip(x, y, x + w, y + h)
    cv.vgrad(x, y, w, h, (180, 210, 225), (225, 235, 238))
    # globe
    cx, cy = x + int(w * 0.30), y + int(h * 0.46)
    r = int(h * 0.34)
    cv.disc(cx, cy, r, (44, 110, 170))
    for ox, oy, orr in [(-0.30, -0.25, 0.32), (0.25, 0.15, 0.28),
                        (0.05, 0.35, 0.22)]:
        cv.disc(cx + int(r * ox), cy + int(r * oy), int(r * orr),
                (70, 150, 90))
    cv.ellipse(cx, cy, r, r, (24, 80, 140))
    # draft paper, bottom right
    px = x + int(w * 0.56)
    py = y + int(h * 0.30)
    pw, ph = int(w * 0.38), int(h * 0.52)
    cv.rect(px, py, pw, ph, WHITE)
    cv.rect(px, py, pw, 3, INK)
    for i in range(4):
        cv.rect(px + 8, py + 12 + i * 12, pw - 16 - i * 8, 3, GREY_LT)
    cv.line(px + 8, py + ph - 12, px + pw - 8, py + ph - 12, 3, RED)
    cv.reset_clip()


def scene_nvidia(cv, x, y, w, h):
    cv.set_clip(x, y, x + w, y + h)
    cv.rect(x, y, w, h, GREEN_DK)
    # chip
    cx, cy = x + w // 2, y + int(h * 0.44)
    cw_, ch_ = int(w * 0.52), int(h * 0.52)
    for i in range(5):
        cv.rect(cx - cw_ // 2 - 10, cy - ch_ // 2 + i * (ch_ // 4),
                10, 6, GOLD)
        cv.rect(cx + cw_ // 2, cy - ch_ // 2 + i * (ch_ // 4), 10, 6,
                GOLD)
    cv.rect(cx - cw_ // 2, cy - ch_ // 2, cw_, ch_, (12, 40, 26))
    cv.rect(cx - cw_ // 2, cy - ch_ // 2, cw_, 4, GREEN)
    cv.rect(cx - cw_ // 2, cy - ch_ // 2, 4, ch_, GREEN)
    draw_text(cv, cx, cy - 12, "NVDA", 24, (120, 220, 140), weight=1.5,
              cw=0.9, align="c")
    draw_text(cv, cx, y + int(h * 0.76), "Q3 RECORD", 16, GOLD,
              weight=1.3, cw=0.9, align="c")
    cv.reset_clip()


# ---------------------------------------------------------------- world map
LAND = [
    # (lon0, lat0, lon1, lat1) rectangles approximating continents
    (-168, 72, -95, 50), (-95, 70, -55, 45), (-125, 49, -66, 25),
    (-117, 32, -83, 8), (-78, 12, -50, -5), (-70, -5, -40, -35),
    (-70, -35, -55, -55), (-58, 84, -20, 60), (-11, 70, 32, 36),
    (-17, 32, 32, 5), (10, 5, 50, -35), (43, -12, 50, -25),
    (35, 42, 60, 12), (60, 75, 135, 50), (135, 75, 180, 42),
    (68, 35, 90, 8), (95, 28, 105, 5), (95, 5, 140, -10),
    (113, -12, 154, -38), (166, -34, 178, -47), (130, 45, 145, 30),
    (-5, 58, 2, 50),
]


def _is_land(lon, lat):
    for (lo0, la0, lo1, la1) in LAND:
        if lo0 <= lon <= lo1 and la1 <= lat <= la0:
            return True
    return False


def draw_map(cv, x, y, w, h, pins):
    """Dotted world map; pins = list of (lon, lat, number)."""
    cv.set_clip(x, y, x + w, y + h)
    cv.rect(x, y, w, h, (232, 238, 244))
    step = 11
    for gy in range(y + 6, y + h - 4, step):
        lat = 75 - (gy - y) / h * 135.0
        for gx in range(x + 6, x + w - 4, step):
            lon = -170 + (gx - x) / w * 360.0
            if _is_land(lon, lat):
                cv.disc(gx, gy, 3, (52, 84, 140))
    for (lon, lat, num, dx, dy) in pins:
        px = x + int((lon + 170) / 360.0 * w) + dx
        py = y + int((75 - lat) / 135.0 * h) + dy
        cv.disc(px, py, 11, RED)
        draw_text(cv, px, py - 7, str(num), 14, WHITE, weight=1.6,
                  cw=0.9, align="c")
    cv.reset_clip()

# ---------------------------------------------------------------- story data
# All 40 stories happened, or were first reported, on 19 November 2026.
# Lead facts were re-derived from same-day reporting (see notes): the
# Shenzhen summit, Anthropic's $81.34bn IPO, GTA VI launch, Kerch
# bridge third strike, ICJ Myanmar verdict, IEA Hormuz warning,
# Jeffries 251-11, Cyclone Akvan, Florida record flood, COP31 draft,
# Nvidia board decision, EU 45bn euro loan, Gaza yellow line.

CARDS = [
    dict(num=1, kicker="SHENZHEN \u2022 APEC \u2022 90 MINUTES",
         head="THREE LEADERS, ONE ROOM",
         body="FIRST-EVER TRILATERAL TALKS AT APEC IN SHENZHEN: 90 MINUTES "
              "ON UKRAINE, IRAN AND NUCLEAR ARMS. NO BREAKTHROUGH - BUT A "
              "PLEDGE TO KEEP TALKING.",
         tag="CONFIRMED", tagcol=GREEN, scene="summit"),
    dict(num=2, kicker="VICE CITY \u2022 LEONIDA",
         head="GTA VI IS OUT",
         body="ROCKSTAR'S EPIC LANDS ON PS5 AND XBOX: VICE CITY, JASON AND "
              "LUCIA, A 99 ON METACRITIC.",
         tag="CONFIRMED", tagcol=GREEN, scene="gta"),
    dict(num=3, kicker="TECH",
         head="ANTHROPIC'S $81BN DEBUT",
         body="CLAUDE MAKER PRICES AT $83 IN THE BIGGEST IPO EVER. SHARES "
              "JUMP 34% ON DEBUT.",
         tag="CONFIRMED", tagcol=GREEN, scene="chart"),
    dict(num=4, kicker="JUSTICE",
         head="MYANMAR GUILTY OF GENOCIDE",
         body="WORLD COURT: MYANMAR COMMITTED GENOCIDE IN 2017, A FIRST. "
              "RETURN ORDERED.",
         tag="CONFIRMED", tagcol=GREEN, scene="icj"),
    dict(num=5, kicker="WAR",
         head="KERCH BRIDGE HIT AGAIN",
         body="THIRD STRIKE IN FOUR DAYS: NEPTUNE MISSILES HIT THE RAIL "
              "SPAN. ROAD OUT, RAIL ON ONE LINE.",
         tag="REPORTED", tagcol=(176, 130, 20), scene="kerch"),
    dict(num=6, kicker="ENERGY",
         head="HORMUZ: LARGEST ENERGY THREAT EVER",
         body="IEA: 2.8BN BARRELS LOST; FLOWS MAY FALL TO 2M.",
         tag="CONFIRMED", tagcol=GREEN, scene="gulf"),
    dict(num=7, kicker="WASHINGTON",
         head="JEFFRIES 251-11",
         body="DEMOCRATS PICK JEFFRIES, FIRST BLACK SPEAKER NOMINEE. "
              "VOTE JAN 3.",
         tag="CONFIRMED", tagcol=GREEN, scene="capitol"),
    dict(num=8, kicker="GAZA",
         head="TANKS CROSS THE YELLOW LINE",
         body="ISRAELI TANKS ENTER CENTRAL GAZA IN A RARE RAID.",
         tag="REPORTED", tagcol=(176, 130, 20), scene="gaza"),
    dict(num=9, kicker="UKRAINE",
         head="EU OFFERS 45BN EURO LOAN",
         body="EU LOAN TO CLOSE KYIV'S 70BN EURO GAP.",
         tag="CONFIRMED", tagcol=GREEN, scene="eu"),
    dict(num=10, kicker="WEATHER",
         head="CYCLONE AKVAN BEARS DOWN",
         body="SEVERE STORM NEARS ANDHRA AND ODISHA, LANDFALL FRI NOON, "
              "WINDS 120-130 KM/H.",
         tag=None, tagcol=None, scene="akvan"),
    dict(num=11, kicker="WEATHER",
         head="FLORIDA'S RECORD FLOOD",
         body="ST JOHNS RIVER TOPS ITS 1953 RECORD AT 18.95 FT; SCHOOLS "
              "SHUT, GUARD OUT.",
         tag=None, tagcol=None, scene="florida"),
    dict(num=12, kicker="CLIMATE",
         head="COP31 DRAFT DROPS FOSSIL FUELS",
         body="ANTALYA DRAFT DROPS THE PHASE-OUT LANGUAGE; 1.5C WILL BE "
              "OVERSHOT, IT ADMITS.",
         tag=None, tagcol=None, scene="cop31"),
    dict(num=13, kicker="TECH",
         head="NVIDIA: HUANG WILL NOT RETURN",
         body="BOARD: OUSTED FOUNDER STAYS OUT. Q3 SALES HIT A RECORD "
              "$115.8BN.",
         tag=None, tagcol=None, scene="nvidia"),
]

SCENES = {
    "summit": scene_summit, "gta": scene_gta, "chart": scene_chart,
    "icj": scene_icj, "kerch": scene_kerch, "gulf": scene_gulf,
    "capitol": scene_capitol, "gaza": scene_gaza, "eu": scene_eu,
    "akvan": scene_akvan, "florida": scene_florida, "cop31": scene_cop31,
    "nvidia": scene_nvidia,
}

INDEX = [
    "GOLD $3,713, A 14-MONTH LOW; BRENT $92",
    "HORMUZ SHIPPING NEAR PRE-WAR LEVELS",
    "BOJ SIGNALS A DECEMBER HIKE; RATE 1.25%",
    "UK SENDS 1,000 DRONES TO KYIV",
    "VAN GOGH SELLS FOR $190.4M, ARTIST RECORD",
    "WALMART REVENUE $188.8BN, UP 5.2%",
    "DENMARK APPROVES GREENLAND-US PACT, 109-0",
    "US SENATE REJECTS IRAN WAR POWERS, 51-48",
    "TRUMP PARDONS PETE ROSE, POSTHUMOUS",
    "AUSTRALIA JOBLESS HIGHEST SINCE 2021",
    "SOUTH AFRICA HOLDS RATE AT 7.25%",
    "JAPAN INFLATION ACCELERATES",
    "US JOBLESS CLAIMS RISE UNEXPECTEDLY",
    "DIESEL PRICES TO KEEP FALLING",
    "IRAN WIDENS GULF ATTACKS; KUWAIT REPELS STRIKE",
    "RUSSIAN BOMBERS RETURN TO VIETNAM",
    "ETHIOPIA, ERITREA MASS TROOPS ON BORDER",
    "BANGLADESH: YUNUS HOME TORCHED, 28 DISTRICTS HIT",
    "US, VENEZUELA SIGN MILITARY PACT",
    "TRUMP: TOO BUSY FOR ANOTHER KIM MEETING",
    "GEORGIA GAS BLAST KILLS SIX",
    "PENTAGON PLANS LASER WEAPONS TEST",
    "WHITE HOUSE FIRES CYBER CHIEF CAIRNCROSS",
    "IRAN WAR COSTS TOP $48BN",
    "PUTIN PROPOSES MOSCOW TALKS WITH EUROPE",
    "MUSK BREAKS WITH REPUBLICANS AFTER LOSSES",
    "MARKETS: S&P -0.2%, NASDAQ +0.4%, NIKKEI +0.7%",
]

NUMBERS = [
    ("90 MIN", "SUMMIT TALKS"),
    ("$81.3BN", "ANTHROPIC IPO"),
    ("99", "GTA VI METACRITIC"),
    ("$3,713", "GOLD, 14-MONTH LOW"),
    ("18.95 FT", "ST JOHNS RIVER"),
    ("251-11", "JEFFRIES VOTE"),
]

TIMELINE = [
    ("00:00", "GTA VI UNLOCKS WORLDWIDE"),
    ("01:35", "BOJ'S UEDA SIGNALS HIKES"),
    ("06:00", "SUMMIT OPENS IN SHENZHEN"),
    ("09:00", "ICJ: MYANMAR GUILTY"),
    ("10:50", "IEA WARNS ON HORMUZ"),
    ("12:13", "COP31 DROPS FOSSIL FUELS"),
    ("14:30", "ANTHROPIC OPENS +34%"),
]

PINS = [
    (114.1, 22.5, 1, 0, 0), (-80.2, 25.8, 2, 0, 0),
    (-74.0, 40.7, 3, 0, 0), (4.3, 52.1, 4, -16, -10),
    (35.4, 45.3, 5, 0, 0), (56.5, 26.5, 6, 0, 0),
    (-77.0, 38.9, 7, 0, 0), (34.5, 31.5, 8, 0, 0),
    (4.35, 50.85, 9, 18, 14), (80.3, 15.9, 10, 0, 0),
    (-81.65, 30.3, 11, 18, -12), (30.7, 36.9, 12, 0, 0),
    (-121.0, 37.4, 13, 0, 0),
]


def card(cv, x, y, w, h, c, head_size, body_size, scene_h):
    """Card with a scene on top and text below."""
    card_frame(cv, x, y, w, h)
    SCENES[c["scene"]](cv, x + 2, y + 2, w - 4, scene_h)
    ty = y + 2 + scene_h + 10
    draw_text(cv, x + 12, ty, c["kicker"], 17, RED, weight=1.4, cw=0.92)
    if c["tag"]:
        tw = int(text_w(c["tag"], 15, cw=0.92) + 14)
        tag(cv, x + w - 12 - tw, ty - 2, c["tag"], c["tagcol"], size=15)
    hy = ty + 26
    hlines = wrap(c["head"], head_size, w - 24, cw=0.95)
    hlh = int(head_size * 1.15)
    for i, ln in enumerate(hlines):
        draw_text(cv, x + 12, hy + i * hlh, ln, head_size, NAVY,
                  weight=1.5, cw=0.95)
    by = hy + len(hlines) * hlh + 6
    blines = wrap(c["body"], body_size, w - 24, cw=0.92)
    draw_para(cv, x + 12, by, blines, body_size, int(body_size * 1.22),
              INK, weight=1.0, cw=0.92)


def side_card(cv, x, y, w, h, c):
    """Card with a scene on the left and text on the right."""
    card_frame(cv, x, y, w, h)
    sw = 280
    SCENES[c["scene"]](cv, x + 2, y + 2, sw, h - 4)
    tx = x + sw + 14
    tw = w - sw - 26
    draw_text(cv, tx, y + 12, c["kicker"], 16, RED, weight=1.4, cw=0.92)
    if c["tag"]:
        tgw = int(text_w(c["tag"], 14, cw=0.92) + 14)
        tag(cv, x + w - 12 - tgw, y + 10, c["tag"], c["tagcol"], size=14)
    hlines = wrap(c["head"], 21, tw, cw=0.95)
    for i, ln in enumerate(hlines):
        draw_text(cv, tx, y + 40 + i * 24, ln, 21, NAVY, weight=1.5,
                  cw=0.95)
    by = y + 40 + len(hlines) * 24 + 6
    blines = wrap(c["body"], 16, tw, cw=0.92)
    draw_para(cv, tx, by, blines, 16, 20, INK, weight=1.0, cw=0.92)

# ---------------------------------------------------------------- composition
def build():
    cv = Canvas(W, H)
    cv.rect(0, 0, W, H, PAPER)

    # masthead
    cv.rect(0, 0, W, 112, NAVY)
    draw_text(cv, 40, 28, "THE WORLD TODAY", 58, WHITE, weight=1.25,
              spacing=3)
    draw_text(cv, W - 40, 22, "THURSDAY EDITION", 26, WHITE, weight=1.3,
              align="r")
    draw_text(cv, W - 40, 60, "ONE DAY \u2022 ONE PAGE \u2022 NO. 324", 20,
              GOLD_LT, weight=1.2, align="r")
    cv.rect(0, 112, W, 6, RED)

    # kicker line
    draw_text(cv, 40, 124, "THE WORLD IN ONE DAY", 20, RED, weight=1.5)
    draw_text(cv, W - 40, 124,
              "40 STORIES \u2022 7 REGIONS \u2022 13 DRAWN SCENES", 20, GREY,
              weight=1.2, align="r")

    # date headline + red date box
    draw_text(cv, 40, 148, "THURSDAY 19 NOVEMBER 2026", 84, NAVY,
              weight=1.35, spacing=2)
    cv.rect(1740, 140, 268, 92, RED)
    draw_text(cv, 1874, 152, "NOV 19", 46, WHITE, weight=1.7, align="c")
    draw_text(cv, 1874, 198, "2026", 30, WHITE, weight=1.3, align="c")

    # hero row: summit + GTA VI
    card(cv, 40, 232, 1220, 340, CARDS[0], 34, 20, 208)
    card(cv, 1280, 232, 728, 340, CARDS[1], 34, 20, 208)

    # row 2: Anthropic, ICJ, Kerch
    card(cv, 40, 572, 660, 340, CARDS[2], 28, 20, 160)
    card(cv, 720, 572, 620, 340, CARDS[3], 28, 20, 160)
    card(cv, 1360, 572, 648, 340, CARDS[4], 28, 20, 160)

    # row 3: world map + Hormuz + Jeffries
    draw_text(cv, 40, 924, "WHERE IT HAPPENED", 18, RED, weight=1.4,
              cw=0.92)
    draw_map(cv, 40, 948, 1220, 264, PINS)
    draw_text(cv, 40, 1216,
              "NUMBERS MATCH THE STORY CARDS \u2022 DOTTED MAP: EACH DOT "
              "IS LAND", 14, GREY, weight=1.1, cw=0.92)
    side_card(cv, 1280, 912, 728, 160, CARDS[5])
    side_card(cv, 1280, 1072, 728, 160, CARDS[6])

    # row 4: six small cards
    xs = [40, 371, 702, 1033, 1364, 1695]
    for i, cx in enumerate(xs):
        card(cv, cx, 1232, 311, 280, CARDS[7 + i], 18, 15, 126)

    # numbers strip
    cv.rect(0, 1512, W, 112, NAVY)
    cw_ = 1968 // 6
    for i, (num, lab) in enumerate(NUMBERS):
        cx = 40 + i * cw_ + cw_ // 2
        draw_text(cv, cx, 1530, num, 42, WHITE, weight=1.6, align="c")
        draw_text(cv, cx, 1588, lab, 15, GOLD_LT, weight=1.2, cw=0.9,
                  align="c")
        if i:
            cv.rect(40 + i * cw_, 1530, 2, 76, (60, 76, 120))

    # UTC timeline
    draw_text(cv, 40, 1644, "THE DAY IN UTC", 18, RED, weight=1.4,
              cw=0.92)
    line1 = TIMELINE[:4]
    line2 = TIMELINE[4:]
    for row, items in enumerate([line1, line2]):
        xx = 40
        yy = 1676 + row * 26
        for (t, txt) in items:
            draw_text(cv, xx, yy, t, 17, RED, weight=1.4, cw=0.9)
            tw = text_w(t, 17, cw=0.9)
            draw_text(cv, xx + tw + 8, yy, txt, 17, INK, weight=1.1,
                      cw=0.9)
            xx += tw + 8 + text_w(txt, 17, cw=0.9) + 44

    # index: the rest of the day, 27 more stories
    draw_text(cv, 40, 1736, "THE REST OF THE DAY \u2014 27 MORE STORIES",
              18, RED, weight=1.4, cw=0.92)
    hrule(cv, 40, 1762, 1968, INK, 2)
    colx = [40, 700, 1360]
    for ci in range(3):
        for ri in range(9):
            idx = ci * 9 + ri
            item = INDEX[idx]
            yy = 1778 + ri * 23
            num = str(14 + idx)
            draw_text(cv, colx[ci], yy, num, 15, RED, weight=1.5, cw=0.9)
            nw = text_w(num, 15, cw=0.9)
            draw_text(cv, colx[ci] + nw + 8, yy, item, 15, INK,
                      weight=1.0, cw=0.92)

    # DATE CHECK footer
    cv.rect(0, 1960, W, 56, RED)
    draw_text(cv, W // 2, 1978,
              "DATE CHECK : THURSDAY 19 NOVEMBER 2026 \u2014 EVERY STORY "
              "ABOVE HAPPENED, OR WAS FIRST REPORTED, ON 19 NOV 2026",
              20, WHITE, weight=1.4, cw=0.92, align="c")

    # sources line
    draw_text(cv, 40, 2026,
              "SOURCES: AP, REUTERS, AFP, NYT, BLOOMBERG, ICJ, IEA, IMD, "
              "NWS \u2014 DRAWN FROM REPORTS; NO PHOTOGRAPHS", 14, GREY,
              weight=1.0, cw=0.9)
    draw_text(cv, W - 40, 2026, "EXC-ANA", 14, GREY, weight=1.2, cw=0.9,
              align="r")
    return cv


def main():
    cv = build()
    rgb = downsample(cv)
    data = png_bytes(rgb, 1024, 1024)
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
