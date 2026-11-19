#!/usr/bin/env python3
"""news-image-20261118: sum up Wednesday 18 November 2026 in one image.

Draws a newspaper front page (1024x1024 PNG) with pure Python 3 stdlib
only -- no PIL, no network, no external assets -- so it runs identically
in the make.fun sandbox (stdlib only) and on any local Python 3.

Layout (PLAN.md art direction, drawn live by this program):
  masthead "WEDNESDAY 18 NOVEMBER 2026", red rule,
  hero: Kerch Bridge in daylight -- collapsed road span hanging into the
  strait, smoke, and a train crossing the surviving rail section,
  headline "THE BRIDGE, BROKEN",
  subline "Road span down in the strait -- trains run on; 141 drones
  overnight",
  bottom strip, three equal mini-stories: Gulf, Shenzhen, Voyager 1.

Deterministic: fixed palette, fixed geometry, no time, no randomness,
PNG written with zlib level 9 and no ancillary chunks, so two runs
produce byte-identical output.
"""

import binascii
import math
import os
import struct
import sys
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
CREAM = (246, 238, 214)   # newsprint background
INK = (20, 20, 20)        # type and line work
RED = (193, 39, 45)       # the one red accent: the lead story only
SKY = (199, 220, 234)
SEA = (78, 127, 166)
SEA_DARK = (38, 80, 130)
SAND = (222, 205, 160)
GREY = (96, 96, 96)
SMOKE = (150, 150, 150)
STEEL = (58, 58, 58)
WHITE = (255, 255, 255)
NIGHT = (10, 10, 18)
PALE = (214, 228, 245)    # the one pale dot: Earth, one light-day away

# ------------------------------------------------------- stroke font
# Hand-built single-stroke capitals on a 10 x 12 grid (y down, baseline
# y=12; descenders to y=14). Each glyph is a list of strokes; each stroke
# is a list of (x, y) points joined by straight segments. Rendered thick,
# it reads as a clean bold sans at any scale.
FONT = {
    "A": [[(1, 12), (5, 0), (9, 12)], [(3, 8), (7, 8)]],
    "B": [[(1, 0), (1, 12)],
          [(1, 0), (6, 0), (8, 2), (8, 4), (6, 6), (1, 6)],
          [(1, 6), (6, 6), (8, 8), (8, 10), (6, 12), (1, 12)]],
    "C": [[(8, 2), (6, 0), (3, 0), (1, 2), (1, 10), (3, 12), (6, 12), (8, 10)]],
    "D": [[(1, 0), (1, 12)], [(1, 0), (6, 0), (8, 2), (8, 10), (6, 12), (1, 12)]],
    "E": [[(8, 0), (1, 0), (1, 12), (8, 12)], [(1, 6), (6, 6)]],
    "F": [[(8, 0), (1, 0), (1, 12)], [(1, 6), (6, 6)]],
    "G": [[(8, 2), (6, 0), (3, 0), (1, 2), (1, 10), (3, 12), (6, 12),
           (8, 10), (8, 7), (5, 7)]],
    "H": [[(1, 0), (1, 12)], [(9, 0), (9, 12)], [(1, 6), (9, 6)]],
    "I": [[(5, 0), (5, 12)], [(2, 0), (8, 0)], [(2, 12), (8, 12)]],
    "J": [[(8, 0), (8, 9), (6, 12), (2, 12), (1, 10)]],
    "K": [[(1, 0), (1, 12)], [(9, 0), (1, 6)], [(4, 5), (9, 12)]],
    "L": [[(1, 0), (1, 12), (8, 12)]],
    "M": [[(1, 12), (1, 0), (5, 7), (9, 0), (9, 12)]],
    "N": [[(1, 12), (1, 0), (9, 12), (9, 0)]],
    "O": [[(3, 0), (7, 0), (9, 2), (9, 10), (7, 12), (3, 12), (1, 10),
           (1, 2), (3, 0)]],
    "P": [[(1, 12), (1, 0), (7, 0), (9, 2), (9, 5), (7, 7), (1, 7)]],
    "Q": [[(3, 0), (7, 0), (9, 2), (9, 10), (7, 12), (3, 12), (1, 10),
           (1, 2), (3, 0)], [(6, 9), (9, 13)]],
    "R": [[(1, 12), (1, 0), (7, 0), (9, 2), (9, 5), (7, 7), (1, 7)],
          [(6, 7), (9, 12)]],
    "S": [[(8, 2), (6, 0), (3, 0), (1, 2), (1, 5), (3, 7), (7, 7), (9, 9),
           (9, 10), (7, 12), (3, 12), (1, 10)]],
    "T": [[(1, 0), (9, 0)], [(5, 0), (5, 12)]],
    "U": [[(1, 0), (1, 9), (3, 12), (7, 12), (9, 9), (9, 0)]],
    "V": [[(1, 0), (5, 12), (9, 0)]],
    "W": [[(1, 0), (3, 12), (5, 6), (7, 12), (9, 0)]],
    "X": [[(1, 0), (9, 12)], [(9, 0), (1, 12)]],
    "Y": [[(1, 0), (5, 6), (9, 0)], [(5, 6), (5, 12)]],
    "Z": [[(1, 0), (9, 0), (1, 12), (9, 12)]],
    "0": [[(3, 0), (7, 0), (9, 2), (9, 10), (7, 12), (3, 12), (1, 10),
           (1, 2), (3, 0)]],
    "1": [[(3, 2), (5, 0), (5, 12)], [(2, 12), (8, 12)]],
    "2": [[(1, 2), (3, 0), (7, 0), (9, 2), (9, 5), (1, 12), (9, 12)]],
    "3": [[(2, 0), (7, 0), (9, 2), (9, 5), (7, 7)],
          [(7, 7), (9, 9), (9, 11), (7, 12), (2, 12)]],
    "4": [[(6, 0), (6, 12)], [(0, 8), (8, 8)], [(6, 0), (0, 8)]],
    "5": [[(8, 0), (1, 0), (1, 6), (7, 6), (9, 8), (9, 10), (7, 12), (1, 12)]],
    "6": [[(8, 1), (6, 0), (3, 0), (1, 2), (1, 10), (3, 12), (6, 12),
           (8, 10), (8, 8), (6, 6), (1, 6)]],
    "7": [[(1, 0), (9, 0), (5, 12)]],
    "8": [[(3, 0), (7, 0), (9, 2), (9, 5), (7, 7), (3, 7), (1, 5), (1, 2),
           (3, 0)],
          [(3, 7), (7, 7), (9, 9), (9, 11), (7, 12), (3, 12), (1, 10),
           (1, 9), (3, 7)]],
    "9": [[(1, 8), (1, 5), (3, 0), (7, 0), (9, 2), (9, 10), (7, 12),
           (3, 12), (1, 10)]],
    " ": [],
    ",": [[(5, 10), (5, 12), (3, 14)]],
    ".": [[(4, 11), (6, 11), (6, 13), (4, 13), (4, 11)]],
    "'": [[(5, 0), (4, 4)]],
    "-": [[(1, 6), (9, 6)]],
    "\u2014": [[(0, 6), (10, 6)]],
    ":": [[(4, 3), (6, 3), (6, 5), (4, 5), (4, 3)],
          [(4, 9), (6, 9), (6, 11), (4, 11), (4, 9)]],
    ";": [[(4, 3), (6, 3), (6, 5), (4, 5), (4, 3)],
          [(5, 8), (5, 11), (3, 13)]],
    "/": [[(8, 12), (2, 0)]],
    "!": [[(5, 0), (5, 8)], [(4, 10), (6, 10), (6, 12), (4, 12), (4, 10)]],
    "?": [[(2, 2), (4, 0), (7, 0), (9, 2), (9, 4), (7, 6), (5, 6), (5, 8)],
          [(4, 10), (6, 10), (6, 12), (4, 12), (4, 10)]],
    "(": [[(7, 0), (4, 3), (4, 9), (7, 12)]],
    ")": [[(3, 0), (6, 3), (6, 9), (3, 12)]],
    "\u2022": [[(4, 5), (6, 5), (6, 7), (4, 7), (4, 5)]],
}

ADVANCE = 11.0  # glyph cell width in font units, including the gap


def text_width(text, scale):
    """Pixel width of `text` at the given scale."""
    return len(text) * ADVANCE * scale


# ---------------------------------------------------------------- canvas
class Canvas:
    """A plain RGB raster; every draw op clips to the frame."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bytes(bg) * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def fill_rect(self, x0, y0, x1, y1, color):
        x0 = max(0, int(x0)); y0 = max(0, int(y0))
        x1 = min(self.w, int(x1)); y1 = min(self.h, int(y1))
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for y in range(y0, y1):
            i = (y * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def fill_circle(self, cx, cy, r, color):
        r = int(r)
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.fill_rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, color)

    def disc(self, cx, cy, r, color):
        self.fill_circle(cx, cy, r, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        """Bresenham line stamped with a disc of radius thick//2."""
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        r = max(0, thick // 2)
        dx = abs(x1 - x0); dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.disc(x0, y0, r, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy; x0 += sx
            if e2 <= dx:
                err += dx; y0 += sy

    def polyline(self, points, color, thick=1):
        for (ax, ay), (bx, by) in zip(points, points[1:]):
            self.line(ax, ay, bx, by, color, thick)

    def polygon(self, points, color):
        """Scanline fill of a simple polygon (even-odd rule)."""
        if len(points) < 3:
            return
        ys = [p[1] for p in points]
        y0, y1 = int(math.ceil(min(ys))), int(math.floor(max(ys)))
        n = len(points)
        for y in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                ax, ay = points[i]
                bx, by = points[(i + 1) % n]
                if (ay <= y < by) or (by <= y < ay):
                    t = (y - ay) / (by - ay)
                    xs.append(ax + t * (bx - ax))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.fill_rect(int(math.ceil(xs[j])), y,
                               int(math.floor(xs[j + 1])) + 1, y + 1, color)

    def ellipse(self, cx, cy, rx, ry, color):
        for dy in range(-int(ry), int(ry) + 1):
            t = 1.0 - (dy * dy) / float(ry * ry)
            dx = int(rx * math.sqrt(max(0.0, t)))
            self.fill_rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, color)

    def ring(self, cx, cy, r, color, thick=2):
        for a in range(0, 360, 2):
            t = math.radians(a)
            self.disc(int(cx + r * math.cos(t)), int(cy + r * math.sin(t)),
                      max(0, thick // 2), color)

    # ------------------------------------------------------------ text
    def text(self, x, y, scale, color, s, thick=None):
        """Draw `s` (already upper-case) with top-left at (x, y)."""
        if thick is None:
            thick = max(1, int(round(scale * 0.85)))
        cx = float(x)
        for ch in s:
            for stroke in FONT.get(ch, FONT.get("?", [])):
                pts = [(cx + px * scale, y + py * scale) for (px, py) in stroke]
                self.polyline(pts, color, thick)
            cx += ADVANCE * scale

    def text_centered(self, cx, y, scale, color, s, thick=None):
        self.text(cx - text_width(s, scale) / 2.0, y, scale, color, s, thick)


# ---------------------------------------------------------------- PNG
def png_bytes(canvas):
    """Encode the canvas as a deterministic PNG (no ancillary chunks)."""
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)  # filter: none
        raw += canvas.px[y * stride:(y + 1) * stride]
    data = zlib.compress(bytes(raw), 9)

    def chunk(tag, payload):
        out = struct.pack(">I", len(payload)) + tag + payload
        out += struct.pack(">I", binascii.crc32(tag + payload) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", data) + chunk(b"IEND", b""))


# ---------------------------------------------------------------- scenes
def draw_masthead(c):
    c.text_centered(W / 2, 26, 2.6, INK, "WEDNESDAY 18 NOVEMBER 2026")
    c.fill_rect(24, 96, 1000, 102, RED)
    c.fill_rect(24, 106, 1000, 108, INK)
    c.text(24, 122, 1.5, RED, "LEAD STORY")
    c.text(1000 - text_width("KERCH STRAIT", 1.5), 122, 1.5, INK, "KERCH STRAIT")


def draw_hero(c):
    x0, y0, x1, y1 = 24, 150, 1000, 470
    # sky and sea
    c.fill_rect(x0, y0, x1, 332, SKY)
    c.fill_rect(x0, 332, x1, y1, SEA)
    # flat clouds
    c.ellipse(180, 190, 70, 14, WHITE)
    c.ellipse(230, 182, 46, 11, WHITE)
    c.ellipse(860, 180, 80, 15, WHITE)
    c.ellipse(910, 172, 50, 11, WHITE)
    # pale sun
    c.fill_circle(905, 215, 22, (250, 242, 200))
    # waves
    for wy in (352, 382, 418, 448):
        for wx in range(40, 990, 90):
            c.line(wx, wy, wx + 52, wy, (190, 215, 232), 3)
    # --- bridge: surviving road deck (left) + rail deck above it
    c.fill_rect(24, 306, 560, 318, STEEL)          # road deck
    c.fill_rect(24, 292, 560, 300, INK)            # rail deck
    # pylons and cables on the surviving side
    for px in (130, 470):
        c.fill_rect(px, 190, px + 14, 332, STEEL)
        c.fill_rect(px - 4, 184, px + 18, 192, INK)
        c.line(px + 7, 192, px - 90, 300, INK, 2)
        c.line(px + 7, 192, px + 100, 300, INK, 2)
    # --- the collapse: road span torn away, hanging into the strait
    c.polygon([(560, 296), (640, 342), (702, 394), (762, 440), (742, 448),
               (682, 402), (620, 350), (560, 314)], STEEL)
    c.polygon([(560, 296), (600, 320), (560, 314)], INK)
    # broken end of the surviving deck, jagged
    c.polygon([(560, 296), (576, 306), (560, 318), (548, 306)], INK)
    # debris in the water under the break
    for (dx, dy, dw, dh) in ((640, 446, 34, 8), (700, 452, 26, 7),
                             (748, 440, 20, 6), (610, 456, 22, 6)):
        c.fill_rect(dx, dy, dx + dw, dy + dh, STEEL)
    # splash where the span hit the water
    c.fill_circle(760, 442, 10, WHITE)
    c.fill_circle(742, 448, 7, WHITE)
    c.fill_circle(778, 448, 6, WHITE)
    # --- smoke over the gap
    for (sx, sy, sr, col) in ((606, 252, 30, SMOKE), (646, 222, 36, GREY),
                              (688, 250, 28, SMOKE), (626, 232, 20, (180, 180, 180)),
                              (664, 238, 18, (180, 180, 180))):
        c.fill_circle(sx, sy, sr, col)
    # --- the train, running on the surviving rail (the twist of the day)
    ty = 262
    c.fill_rect(64, ty, 128, 292, INK)             # locomotive
    c.fill_rect(64, ty, 128, ty + 8, RED)          # loco stripe: lead red
    c.fill_rect(112, ty - 14, 126, ty, INK)        # chimney
    c.fill_rect(72, ty + 10, 92, ty + 20, CREAM)   # cab window
    for i, cx in enumerate((140, 260, 380)):
        c.fill_rect(cx, ty + 4, cx + 108, 292, STEEL)   # carriage
        c.fill_rect(cx, ty + 4, cx + 108, ty + 10, CREAM)
        for wx in range(cx + 12, cx + 100, 24):
            c.fill_rect(wx, ty + 14, wx + 12, ty + 24, CREAM)
    for wx in (80, 112, 160, 200, 240, 280, 320, 360, 400, 440, 470):
        c.fill_circle(wx, 294, 5, INK)
    # headline + subline under the picture
    c.text_centered(W / 2, 492, 4.5, RED, "THE BRIDGE, BROKEN")
    c.text_centered(W / 2, 566, 1.9, INK, "ROAD SPAN DOWN IN THE STRAIT \u2014")
    c.text_centered(W / 2, 596, 1.9, INK, "TRAINS RUN ON; 141 DRONES OVERNIGHT")


def draw_gulf(c, x0, w):
    """Mini-story 1: missile/drone trails over a strait map."""
    y0, y1 = 700, 850
    c.fill_rect(x0, y0, x0 + w, y1, SEA_DARK)
    # land masses, sand, leaving a diagonal strait channel
    c.polygon([(x0, y0), (x0 + 190, y0), (x0 + 120, y0 + 70),
               (x0 + 40, y0 + 70), (x0, y0 + 40)], SAND)
    c.polygon([(x0 + w, y1), (x0 + w - 40, y1 - 50), (x0 + 150, y1 - 55),
               (x0 + 200, y1), (x0 + w, y1)], SAND)
    # strait channel: pale water line between the lands
    c.line(x0 + 60, y0 + 62, x0 + w - 60, y1 - 48, (190, 215, 232), 4)
    # missile / drone trails: white arcs with dots, both directions
    c.polyline([(x0 + 30, y0 + 26), (x0 + 110, y0 + 60), (x0 + 180, y0 + 96),
                (x0 + 250, y0 + 128)], WHITE, 3)
    c.polyline([(x0 + w - 24, y1 - 22), (x0 + w - 110, y1 - 58),
                (x0 + w - 180, y1 - 92)], WHITE, 3)
    for (dx, dy) in ((80, 48), (140, 78), (200, 106), (250, 128),
                     (220, 96), (160, 66)):
        c.fill_circle(x0 + dx, y0 + dy, 4, WHITE)
    # burst where a trail meets the strait
    bx, by = x0 + 150, y0 + 82
    for ang in range(0, 360, 45):
        t = math.radians(ang)
        c.line(bx, by, bx + 16 * math.cos(t), by + 16 * math.sin(t), WHITE, 3)
    c.fill_circle(bx, by, 6, WHITE)
    c.text_centered(x0 + w / 2, y1 - 22, 1.1, WHITE, "STRAIT OF HORMUZ")


def draw_shenzhen(c, x0, w):
    """Mini-story 2: three flags (US, China, Russia) over a skyline."""
    y0, y1 = 700, 850
    c.fill_rect(x0, y0, x0 + w, y1, (232, 226, 208))
    # skyline, ink, along the bottom
    base = y1
    for (bx, bw, bh) in ((8, 34, 52), (48, 26, 78), (80, 40, 44),
                         (126, 30, 92), (162, 36, 60), (204, 28, 84),
                         (238, 40, 48), (284, 12, 30)):
        c.fill_rect(x0 + bx, base - bh, x0 + bx + bw, base, INK)
        for wy in range(base - bh + 8, base - 6, 14):
            for wx in range(x0 + bx + 6, x0 + bx + bw - 6, 12):
                c.fill_rect(wx, wy, wx + 4, wy + 5, CREAM)
    # three flag poles
    poles = [x0 + 60, x0 + w / 2, x0 + w - 60]
    for px in poles:
        c.line(px, y0 + 14, px, y0 + 62, INK, 3)
    # US flag: red/white stripes + blue canton
    fx, fy = poles[0] + 4, y0 + 14
    for i in range(5):
        c.fill_rect(fx, fy + i * 7, fx + 52, fy + i * 7 + 4,
                    RED if i % 2 == 0 else WHITE)
    c.fill_rect(fx, fy, fx + 22, fy + 18, (30, 60, 140))
    # China flag: red field, pale stars
    fx = poles[1] + 4
    c.fill_rect(fx, fy, fx + 52, fy + 34, RED)
    c.fill_circle(fx + 11, fy + 9, 4, (250, 220, 90))
    for (sx, sy) in ((26, 6), (32, 12), (30, 20), (22, 16)):
        c.fill_circle(fx + sx, fy + sy, 2, (250, 220, 90))
    # Russia flag: white / blue / red horizontal thirds
    fx = poles[2] + 4
    c.fill_rect(fx, fy, fx + 52, fy + 12, WHITE)
    c.fill_rect(fx, fy + 12, fx + 52, fy + 23, (30, 60, 160))
    c.fill_rect(fx, fy + 23, fx + 52, fy + 34, RED)


def draw_voyager(c, x0, w):
    """Mini-story 3: a tiny probe in black space, one pale dot far away."""
    y0, y1 = 700, 850
    c.fill_rect(x0, y0, x0 + w, y1, NIGHT)
    # fixed stars
    for (sx, sy, sr) in ((24, 22, 2), (70, 48, 2), (120, 18, 3), (170, 60, 2),
                         (210, 30, 2), (250, 70, 3), (40, 90, 2), (90, 110, 2),
                         (150, 120, 2), (230, 110, 2), (280, 40, 2), (200, 130, 2)):
        c.fill_circle(x0 + sx, y0 + sy, sr, WHITE)
    # the probe, left of centre: dish + body + boom
    px, py = x0 + 78, y0 + 78
    c.polygon([(px, py - 24), (px - 22, py - 50), (px + 22, py - 50)], CREAM)
    c.line(px, py - 24, px, py + 6, CREAM, 3)
    c.fill_rect(px - 16, py + 6, px + 16, py + 28, CREAM)
    c.line(px + 16, py + 16, px + 46, py + 28, CREAM, 3)
    c.fill_circle(px + 48, py + 29, 4, CREAM)
    # thin dotted path from the probe to the pale dot
    for t in range(0, 101, 8):
        dx = px + 60 + t * 1.55
        dy = py - 10 - t * 0.28
        c.fill_circle(int(dx), int(dy), 2, (140, 150, 170))
    # Earth: one pale dot, a full light-day away, ringed
    ex, ey = x0 + w - 52, y0 + 34
    c.fill_circle(ex, ey, 6, PALE)
    c.ring(ex, ey, 13, PALE, 2)


def draw_bottom_strip(c):
    cols = [(24, 312), (356, 312), (688, 312)]
    tags = ["THE GULF", "SHENZHEN", "DEEP SPACE"]
    heads = [("GULF STRIKES", "BACK"),
             ("THREE LEADERS,", "ONE TABLE"),
             ("ONE LIGHT-DAY", "FROM HOME")]
    painters = [draw_gulf, draw_shenzhen, draw_voyager]
    for i, ((x0, w), tag, (h1, h2), paint) in enumerate(
            zip(cols, tags, heads, painters)):
        if i:
            c.fill_rect(x0 - 10, 660, x0 - 8, 990, INK)
        c.text_centered(x0 + w / 2, 668, 1.5, INK, tag)
        paint(c, x0, w)
        c.text_centered(x0 + w / 2, 868, 2.0, INK, h1)
        c.text_centered(x0 + w / 2, 900, 2.0, INK, h2)
    c.fill_rect(24, 640, 1000, 643, INK)
    c.text_centered(W / 2, 992, 1.2, INK, "18 NOVEMBER 2026 \u2014 THE WORLD IN ONE PAGE")


def draw_page():
    c = Canvas(W, H, CREAM)
    # outer frame
    c.fill_rect(0, 0, W, 8, INK)
    c.fill_rect(0, H - 8, W, H, INK)
    c.fill_rect(0, 0, 8, H, INK)
    c.fill_rect(W - 8, 0, W, H, INK)
    draw_masthead(c)
    draw_hero(c)
    draw_bottom_strip(c)
    return c


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(outdir, exist_ok=True)
    data = png_bytes(draw_page())
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
