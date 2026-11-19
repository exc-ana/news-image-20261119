#!/usr/bin/env python3
"""One-page newspaper broadsheet for Thursday 19 November 2026.
40 stories, all first reported that day. 1024x1024 PNG.
Stdlib only, no network, no clock, no randomness. Deterministic.
Own bitmap font, own canvas, own PNG encoder - written fresh here.
"""
import os
import struct
import zlib

W = 1024
H = 1024

NAVY = (11, 31, 75)
NAVY2 = (18, 48, 110)
GOLD = (212, 175, 55)
RED = (192, 28, 28)
RED2 = (220, 45, 45)
LIGHT_BLUE = (165, 205, 255)
GREEN = (28, 120, 60)
ORANGE = (200, 110, 0)
BLUE = (30, 90, 180)
GRAY = (100, 100, 100)
DARK = (20, 20, 20)
LIGHT = (232, 234, 238)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY = (210, 230, 245)
SAND = (245, 235, 200)

FONT = {
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
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
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
}

PIX = bytearray(b"\xff" * (W * H * 3))

CLIP = None


def set_px(x, y, color):
    if CLIP is not None:
        if not (CLIP[0] <= x < CLIP[0] + CLIP[2] and CLIP[1] <= y < CLIP[1] + CLIP[3]):
            return
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        PIX[i] = color[0]
        PIX[i + 1] = color[1]
        PIX[i + 2] = color[2]


def fill_rect(x, y, w, h, color):
    if CLIP is not None:
        x0c = max(x, CLIP[0])
        y0c = max(y, CLIP[1])
        x1c = min(x + w, CLIP[0] + CLIP[2])
        y1c = min(y + h, CLIP[1] + CLIP[3])
        x, y, w, h = x0c, y0c, x1c - x0c, y1c - y0c
        if w <= 0 or h <= 0:
            return
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            PIX[i] = color[0]
            PIX[i + 1] = color[1]
            PIX[i + 2] = color[2]


def rect_outline(x, y, w, h, color):
    fill_rect(x, y, w, 1, color)
    fill_rect(x, y + h - 1, w, 1, color)
    fill_rect(x, y, 1, h, color)
    fill_rect(x + w - 1, y, 1, h, color)


def draw_line(x0, y0, x1, y1, color):
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    x, y = x0, y0
    while True:
        set_px(x, y, color)
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy


def fill_circle(cx, cy, r, color):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            if (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy) <= r * r:
                set_px(xx, yy, color)


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(x, y, s, scale, color):
    s = s.upper()
    cx = x
    for ch in s:
        glyph = FONT.get(ch, FONT[" "])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":
                    fill_rect(cx + col * scale, y + row * scale, scale, scale, color)
        cx += 6 * scale
    return cx


def draw_centered(cx, y, s, scale, color):
    w = text_width(s.upper(), scale)
    draw_text(cx - w // 2, y, s, scale, color)


def wrap_text(text, max_w, scale):
    text = text.upper()
    words = text.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(x, y, text, scale, color, max_w, line_h, max_lines):
    lines = wrap_text(text, max_w, scale)[:max_lines]
    for i, ln in enumerate(lines):
        draw_text(x, y + i * line_h, ln, scale, color)
    return len(lines)


def draw_illus(x, y, w, h, kind):
    global CLIP
    old_clip = CLIP
    CLIP = (x, y, w, h)
    bg = SKY if kind in (2, 7, 11) else SAND if kind in (8,) else (238, 240, 245)
    if kind == 6:
        bg = (30, 30, 55)
    if kind == 10:
        bg = (255, 225, 190)
    fill_rect(x, y, w, h, bg)
    rect_outline(x, y, w, h, (200, 200, 200))
    cx = x + w // 2
    cy = y + h // 2
    if kind == 1:
        fill_rect(x + 8, cy + 6, w - 16, 5, (120, 80, 40))
        for i, off in enumerate((-52, 0, 52)):
            fill_circle(cx + off, cy - 8, 11, (230, 190, 150))
            fill_rect(cx + off - 13, cy + 2, 26, 8, (NAVY if i == 0 else RED if i == 1 else (40, 90, 40)))
        draw_text(x + 6, y + 2, "SHENZHEN", 1, NAVY)
    elif kind == 2:
        fill_rect(x, y + h - 12, w, 12, (30, 90, 160))
        fill_rect(x + 30, cy - 6, w - 90, 16, (40, 40, 40))
        fill_rect(x + 40, cy - 18, 26, 12, (200, 60, 60))
        fill_rect(x + 70, cy - 18, 26, 12, (240, 180, 40))
        draw_line(x + 10, y + h - 6, x + w - 10, y + h - 6, WHITE)
    elif kind == 3:
        fill_rect(x + 14, cy + 4, 12, 12, GREEN)
        fill_rect(x + 34, cy - 2, 12, 18, GREEN)
        fill_rect(x + 54, cy - 10, 12, 26, GREEN)
        draw_line(x + 10, cy - 12, x + w - 20, cy - 18, RED)
        draw_text(x + w - 52, y + 2, "$111", 1, NAVY)
    elif kind == 4:
        fill_rect(x + 8, cy + 2, w - 16, 4, (80, 80, 80))
        fill_rect(x + 30, cy + 6, 6, 12, (80, 80, 80))
        fill_rect(x + w - 40, cy + 6, 6, 12, (80, 80, 80))
        fill_circle(cx, cy - 10, 9, (255, 180, 40))
        fill_circle(cx, cy - 10, 4, RED)
    elif kind == 5:
        fill_rect(cx - 22, cy - 2, 44, h - (cy - y) - 4, (90, 60, 30))
        fill_rect(cx - 30, cy - 14, 60, 6, NAVY)
        fill_circle(cx, cy - 24, 8, (230, 190, 150))
        draw_line(x + w - 18, y + 4, x + w - 18, y + 22, (60, 60, 60))
        fill_rect(x + w - 18, y + 4, 14, 9, RED)
    elif kind == 6:
        for i, bh in enumerate((18, 28, 14, 24, 20)):
            bx = x + 10 + i * 26
            fill_rect(bx, y + h - 8 - bh, 20, bh, (90, 120, 200))
        draw_text(cx - 14, y + 2, "VI", 2, GOLD)
        fill_circle(x + w - 22, y + 10, 6, (255, 220, 90))
    elif kind == 7:
        fill_circle(cx, cy, 12, WHITE)
        fill_circle(cx, cy, 8, SKY)
        fill_circle(cx, cy, 4, NAVY)
        for dx in (-40, -20, 20, 40):
            draw_line(cx + dx, cy - 14, cx + dx - 3, cy - 6, BLUE)
    elif kind == 8:
        fill_rect(x + 16, cy - 2, 30, 12, (212, 175, 55))
        fill_rect(x + 52, cy - 2, 30, 12, (190, 150, 40))
        fill_rect(x + 32, cy - 14, 30, 12, (230, 195, 80))
        fill_circle(x + w - 24, cy, 8, (20, 20, 20))
    elif kind == 9:
        draw_line(cx, y + 4, cx, cy + 10, (120, 90, 40))
        draw_line(cx - 26, y + 8, cx + 26, y + 8, (120, 90, 40))
        fill_rect(cx - 34, y + 8, 16, 4, GOLD)
        fill_rect(cx + 18, y + 8, 16, 4, GOLD)
        fill_rect(cx - 18, cy + 10, 36, 4, (120, 90, 40))
    elif kind == 10:
        fill_circle(cx - 20, cy, 10, (255, 120, 20))
        fill_circle(cx - 20, cy - 4, 6, (255, 200, 40))
        fill_rect(cx + 6, cy - 10, 26, 22, (60, 60, 60))
        fill_rect(cx + 6, cy - 4, 26, 2, (255, 200, 40))
    elif kind == 11:
        fill_rect(x, y + h - 10, w, 10, (30, 110, 200))
        draw_line(x + 8, y + h - 5, x + w - 8, y + h - 5, WHITE)
        fill_rect(cx - 18, cy - 8, 36, 18, (180, 120, 70))
        draw_line(cx - 22, cy - 8, cx, cy - 18, RED)
        draw_line(cx, cy - 18, cx + 22, cy - 8, RED)
    elif kind == 12:
        fill_rect(x + 14, cy - 12, w - 28, 5, NAVY)
        for i in range(4):
            fill_rect(x + 20 + i * 22, cy - 7, 8, 18, NAVY)
        fill_rect(x + 14, cy + 12, w - 28, 4, NAVY)
        draw_line(x + w - 26, cy - 12, x + w - 14, cy - 20, GREEN)
    else:
        for i, col in enumerate((NAVY, RED, (40, 90, 40), GOLD)):
            fx = x + 16 + i * 30
            draw_line(fx, y + 6, fx, y + 26, (60, 60, 60))
            fill_rect(fx, y + 6, 20, 11, col)
    CLIP = old_clip


CARDS = [
    (1, "ASIA - SUMMIT", "CONFIRMED", "TRUMP, XI AND PUTIN MEET IN SHENZHEN",
     "Three leaders hold first-ever three-way talks for 90 minutes; pledge UN reform, more oil output and nuclear dialogue. No breakthrough on Ukraine or Iran."),
    (2, "MIDDLE EAST", "REPORT", "IRAN SEIZES TANKER IN GULF OF OMAN",
     "IRGC says it seized the Ocean Koi in the Gulf of Oman; the US says it disabled two tankers. Trump says Iran hit three US destroyers."),
    (3, "TECH", "CONFIRMED", "ANT OPENS AT $111.50",
     "Anthropic debuts on Nasdaq as ANT, up 34.3% on its $83 IPO price; record $81.3bn raise."),
    (4, "EUROPE - WAR", "REPORT", "KERCH BRIDGE HIT A THIRD TIME",
     "Overnight drone attack hits the rail section; traffic halted. Russia says repairs take two months."),
    (5, "UNITED STATES", "CONFIRMED", "JEFFRIES NOMINATED FOR SPEAKER",
     "House Democrats pick Jeffries 251-11; on course to be the first Black Speaker in January."),
    (6, "CULTURE", "CONFIRMED", "GTA VI OUT WORLDWIDE",
     "Launches at midnight worldwide; Metacritic 99, sales near 19m."),
    (7, "ASIA - WEATHER", "CONFIRMED", "AKVAN: 100,000 EVACUATED",
     "Odisha moves 105,304 people to shelters; landfall due noon Friday."),
    (8, "MARKETS", "CONFIRMED", "GOLD SINKS, OIL EDGES UP",
     "Gold nears $3,713, a 14-month low; Brent $92.87 on Gulf risks."),
    (9, "WORLD", "CONFIRMED", "MYANMAR GUILTY OF GENOCIDE",
     "Top court rules Myanmar committed genocide against the Rohingya."),
    (10, "ENERGY", "REPORT", "HORMUZ TOP ENERGY THREAT EVER",
     "IEA: Hormuz crisis is the biggest energy threat in history."),
    (11, "UNITED STATES", "CONFIRMED", "FLORIDA FLOODS IN FOOT OF RAIN",
     "A foot of rain floods Hollywood, Florida; I-95 shut, rescues on."),
    (12, "ASIA - ECONOMY", "CONFIRMED", "BOJ: MORE RATE RISES COMING",
     "Bank of Japan chief Ueda says the bank will keep raising rates."),
    (13, "EUROPE", "CONFIRMED", "COALITION MEETS IN BERLIN",
     "Ukraine backers meet in Berlin; winter energy ceasefire urged."),
]

INDEX_ITEMS = [
    "ANT FIRST TRADE 11:48 AM ET",
    "90 MINUTES, NO BREAKTHROUGH",
    "TRUMP TO MEET KIM AT SOME POINT",
    "PUTIN BACK AT APEC AFTER 9 YEARS",
    "ALBANESE OBJECTS AT SUMMIT",
    "TRUMP FLIES HOME, PRESSER DUE",
    "OCEAN KOI SEIZED, IRAN SAYS",
    "US DISABLES TWO TANKERS",
    "HORMUZ TRAFFIC DOWN 65%",
    "NEPTUNE MISSILES HIT BRIDGE",
    "BRIDGE REPAIRS: TWO MONTHS",
    "SPEAKER VOTE DUE JAN 3",
    "KNESSET SPEAKER CHALLENGE",
    "GTA VI: 19M COPIES, $1.84BN",
    "METACRITIC 99 FOR GTA VI",
    "7.9M WATCH GTA VI STREAMS",
    "TAKE-TWO SHARES UP 6.2%",
    "AKVAN: RED ALERT, SCHOOLS SHUT",
    "AKVAN WINDS 90-100 KMPH",
    "COP31 TALKS CONTINUE",
    "S&P DOWN 0.23%, NASDAQ UP 0.42%",
    "GOLD $3,713, 14-MONTH LOW",
    "BRENT $92, WTI $82",
    "DOLLAR NEAR 19-MONTH HIGH",
    "BITCOIN BELOW $63,000",
    "NIFTY DOWN 0.31% ON FED FEARS",
    "WALMART EARNINGS DUE",
]


def evidence_color(ev):
    if ev == "CONFIRMED":
        return GREEN
    if ev == "CLAIM":
        return ORANGE
    return BLUE


def draw_card(x, y, w, h, num, tag, ev, headline, body, size):
    fill_rect(x, y, w, h, WHITE)
    rect_outline(x, y, w, h, (180, 180, 180))
    fill_rect(x, y, w, 3, NAVY)
    fill_circle(x + 18, y + 18, 12, RED)
    draw_centered(x + 18, y + 12, str(num), 2 if num < 10 else 1, WHITE)
    draw_text(x + 36, y + 12, tag, 1, NAVY)
    ec = evidence_color(ev)
    pill_w = text_width(ev, 1) + 10
    px = x + w - pill_w - 8
    fill_rect(px, y + 8, pill_w, 12, ec)
    draw_text(px + 5, y + 10, ev, 1, WHITE)
    hl_lines = draw_wrapped(x + 10, y + 30, headline, 2, DARK, w - 20, 16, 2)
    body_y = y + 30 + hl_lines * 16 + 4
    max_body = 3 if size in ("hero", "medium") else 2
    draw_wrapped(x + 10, body_y, body, 1, (50, 50, 50), w - 20, 9, max_body)
    ill_h = 44 if size == "hero" else 28 if size == "medium" else 18
    draw_illus(x + 10, y + h - ill_h - 6, w - 20, ill_h, num)


def png_chunk(ctype, data):
    out = struct.pack(">I", len(data)) + ctype + data
    out += struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)
    return out


def encode_png():
    raw = bytearray()
    for yy in range(H):
        raw.append(0)
        raw.extend(PIX[yy * W * 3:(yy + 1) * W * 3])
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    data = b"\x89PNG\r\n\x1a\n"
    data += png_chunk(b"IHDR", ihdr)
    data += png_chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    data += png_chunk(b"IEND", b"")
    return data


def main():
    fill_rect(0, 0, W, H, WHITE)
    fill_rect(0, 0, W, 102, NAVY)
    fill_rect(0, 102, W, 2, GOLD)
    draw_text(24, 10, "THE DAY IN WORLD NEWS", 2, GOLD)
    draw_text(24, 32, "THURSDAY 19 NOVEMBER 2026", 4, WHITE)
    draw_text(24, 74, "40 STORIES - SIX CONTINENTS - ONE DAY - ALL FIRST REPORTED THURSDAY 19 NOVEMBER 2026", 1, LIGHT_BLUE)
    fill_rect(884, 10, 116, 82, RED)
    rect_outline(884, 10, 116, 82, WHITE)
    draw_centered(942, 20, "NOV 19", 3, WHITE)
    draw_centered(942, 62, "THU - 2026", 1, WHITE)
    nums = [
        ("90", "SUMMIT MINUTES"),
        ("$111.50", "ANT OPENS"),
        ("19M", "GTA VI COPIES"),
        ("105,304", "AKVAN EVACUATED"),
        ("251-11", "JEFFRIES"),
        ("$81.3BN", "IPO RAISE"),
    ]
    for i, (val, lab) in enumerate(nums):
        cx = i * 170 + 85
        if i > 0:
            fill_rect(i * 170, 108, 1, 32, LIGHT)
        draw_centered(cx, 108, val, 2, NAVY)
        draw_centered(cx, 126, lab, 1, GRAY)
    fill_rect(0, 142, W, 2, NAVY)
    draw_card(16, 150, 492, 142, 1, CARDS[0][1], CARDS[0][2], CARDS[0][3], CARDS[0][4], "hero")
    draw_card(516, 150, 492, 142, 2, CARDS[1][1], CARDS[1][2], CARDS[1][3], CARDS[1][4], "hero")
    draw_card(16, 300, 325, 128, 3, CARDS[2][1], CARDS[2][2], CARDS[2][3], CARDS[2][4], "medium")
    draw_card(349, 300, 325, 128, 4, CARDS[3][1], CARDS[3][2], CARDS[3][3], CARDS[3][4], "medium")
    draw_card(682, 300, 326, 128, 5, CARDS[4][1], CARDS[4][2], CARDS[4][3], CARDS[4][4], "medium")
    for i, idx in enumerate((5, 6, 7, 8)):
        c = CARDS[idx]
        draw_card(16 + i * 250, 436, 242, 108, c[0], c[1], c[2], c[3], c[4], "small")
    for i, idx in enumerate((9, 10, 11, 12)):
        c = CARDS[idx]
        draw_card(16 + i * 250, 552, 242, 108, c[0], c[1], c[2], c[3], c[4], "small")
    fill_rect(16, 668, 520, 124, WHITE)
    rect_outline(16, 668, 520, 124, (180, 180, 180))
    draw_text(26, 674, "WHERE IT HAPPENED", 2, NAVY)
    continents = [
        (36, 700, 110, 34), (96, 736, 60, 40), (246, 700, 56, 20),
        (248, 722, 62, 44), (312, 700, 150, 46), (428, 760, 56, 18),
    ]
    for (bx, by, bw, bh) in continents:
        for dy in range(0, bh, 8):
            for dx in range(0, bw, 8):
                fill_rect(bx + dx, by + dy, 3, 3, (170, 180, 195))
    pins = [
        (438, 724), (368, 730), (88, 714), (306, 708), (112, 730),
        (200, 754), (396, 750), (248, 706), (424, 764), (344, 760),
        (126, 752), (470, 718), (280, 722),
    ]
    for i, (px, py) in enumerate(pins, start=1):
        fill_circle(px, py, 8, RED)
        draw_centered(px, py - 3, str(i), 1, WHITE)
    fill_rect(552, 668, 456, 76, WHITE)
    rect_outline(552, 668, 456, 76, (180, 180, 180))
    draw_text(562, 674, "THE DAY IN UTC", 2, NAVY)
    timeline = [
        "MIDNIGHT - GTA VI UNLOCKS WORLDWIDE",
        "03:45 UTC - AKVAN 530 KM OFF GOPALPUR",
        "MORNING - SUMMIT OPENS IN SHENZHEN",
        "16:48 UTC - ANT OPENS AT $111.50",
    ]
    for i, t in enumerate(timeline):
        draw_text(562, 694 + i * 11, t, 1, DARK)
    fill_rect(552, 752, 456, 40, WHITE)
    rect_outline(552, 752, 456, 40, (180, 180, 180))
    draw_text(562, 756, "HOW SURE: GREEN=CONFIRMED  ORANGE=CLAIM  BLUE=REPORT", 1, NAVY)
    fill_rect(562, 772, 10, 7, GREEN)
    draw_text(576, 772, "CONFIRMED - 2+ SOURCES", 1, DARK)
    fill_rect(742, 772, 10, 7, ORANGE)
    draw_text(756, 772, "CLAIM - ONE SIDE", 1, DARK)
    fill_rect(562, 782, 10, 7, BLUE)
    draw_text(576, 782, "REPORT - PRESS REPORTS", 1, DARK)
    draw_text(16, 800, "ALSO ON THURSDAY 19 NOVEMBER", 2, NAVY)
    fill_rect(16, 818, 992, 2, NAVY)
    for col in range(3):
        for row in range(9):
            k = col * 9 + row
            if k < len(INDEX_ITEMS):
                n = 14 + k
                draw_text(16 + col * 336, 826 + row * 9, str(n) + ". " + INDEX_ITEMS[k], 1, DARK)
    fill_rect(0, 912, W, 88, RED)
    draw_centered(512, 918, "DATE CHECK - WHAT WE LEFT OUT AND WHY", 2, WHITE)
    draw_text(24, 938, "LEFT OUT - WEDNESDAY 18 NOVEMBER", 1, (255, 230, 180))
    left_items = [
        "VOYAGER 1 ONE LIGHT-DAY",
        "DOW -561 / EU EUR 45BN LOAN",
        "141 DRONES / TANKS IN NUSEIRAT",
        "535 FACTORIES / EBOLA 11,300+",
        "ALCARAZ IN TURIN / TAME IMPALA 7 ARIAS",
        "COP31 SPLIT",
    ]
    for i, t in enumerate(left_items):
        draw_text(24, 950 + i * 8, "- " + t, 1, WHITE)
    draw_text(540, 938, "NOT YET HAPPENED", 1, (255, 230, 180))
    right_items = [
        "AKVAN LANDFALL: FRI 20 NOV",
        "COP31 CLOSES: FRI 20 NOV",
        "ANT OPTIONS TRADE: MON 23 NOV",
        "IPO CLOSES: FRI 20 NOV",
        "SPEAKER VOTE: JAN 3",
    ]
    for i, t in enumerate(right_items):
        draw_text(540, 950 + i * 8, "- " + t, 1, WHITE)
    draw_centered(512, 1006, "SOURCES: AP, REUTERS, AFP, BBC, AL JAZEERA, NYT, LE MONDE, IMD, IEA, SENSOR TOWER", 1, GRAY)
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, "entry.png")
    with open(outpath, "wb") as f:
        f.write(encode_png())


if __name__ == "__main__":
    main()
