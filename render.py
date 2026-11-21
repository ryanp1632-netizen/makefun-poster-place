"""Render the BALENNE travel poster (an invented island) to poster.png.

Pure Pillow + numpy, drawn at 2x and downsampled to 1024x1024.
Usage: python render.py [out.png]
"""
import math
import random
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

S = 2048           # working size (2x)
OUT = 1024         # final size
HZ = 1250          # horizon line (working px)
FONTS = "C:/Windows/Fonts/"
rng = random.Random(7)


def hexc(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(len(a)))


def vgrad(w, h, stops):
    """Vertical gradient image from [(t, color)] stops."""
    ys = np.linspace(0, 1, h)
    arr = np.zeros((h, w, 4), np.float32)
    for c in range(4):
        xs = [s[0] for s in stops]
        vs = [hexc(s[1])[c] if isinstance(s[1], str) else s[1][c] for s in stops]
        arr[:, :, c] = np.interp(ys, xs, vs)[:, None]
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def paste_fill(base, mask, fill):
    """Composite a flat colour (or an RGBA image) through an L mask."""
    if isinstance(fill, Image.Image):
        layer = fill
    else:
        layer = Image.new("RGBA", base.size, fill)
    base.paste(layer, (0, 0), mask)


def poly_mask(pts, size=(S, S)):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m


def bezier(p0, p1, p2, p3, n=60):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]
        out.append((x, y))
    return out


# ---------------------------------------------------------------- palette
NAVY = "#1b2f45"
DEEP = "#22405a"
TEAL = "#2e7f86"
TURQ = "#3fa3a0"
APRICOT = "#f2a46b"
PEACH = "#f7c99a"
CREAM = "#f6ead2"
CORAL = "#e07a5f"
TERRA = "#c75b3a"
SUN = "#fff1c9"
STONE = "#35566a"
STONE_LIT = "#e29a6f"
LEAF = "#2f5d4a"
BOUG = "#d9487f"


def sky(img):
    g = vgrad(S, HZ, [(0.0, "#1f4064"), (0.30, "#3d6b86"), (0.55, "#c98b7c"),
                       (0.78, "#f0a974"), (1.0, "#fbd9a4")])
    img.paste(g, (0, 0))
    d = ImageDraw.Draw(img)
    # deco banded clouds: long flat lozenges in warm tints
    bands = [(600, 1420, 52, "#f3b98f", 150), (700, 1300, 40, "#f6c79c", 140),
             (845, 980, 30, "#f8d3a8", 120), (380, 700, 22, "#e7a08a", 90)]
    for y, length, th, col, a in bands:
        x0 = rng.randint(-200, 500)
        for k in range(2):
            xs = x0 + k * (length + 520)
            d.rounded_rectangle([xs, y, xs + length, y + th], radius=th // 2, fill=hexc(col, a))
    # small high clouds
    for _ in range(9):
        x = rng.randint(0, S)
        y = rng.randint(150, 650)
        L = rng.randint(120, 340)
        d.rounded_rectangle([x, y, x + L, y + 14], radius=7, fill=hexc("#f9dcb8", 90))


def sun(img):
    cx, cy, r = 1585, HZ - 170, 125
    glow = Image.new("L", (S, S), 0)
    ImageDraw.Draw(glow).ellipse([cx - 520, cy - 520, cx + 520, cy + 520], fill=120)
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    paste_fill(img, glow, hexc("#ffe3ae"))
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    # sun sits on the horizon: clip below it
    ImageDraw.Draw(m).rectangle([0, HZ, S, S], fill=0)
    paste_fill(img, m, hexc(SUN))
    return cx


def mountains(img):
    # far range, hazy mauve, two layers
    pts = [(0, HZ)]
    for x in range(0, S + 1, 64):
        y = HZ - 70 - 60 * math.sin(x / 210.0) - 40 * math.sin(x / 77.0 + 1.3)
        if 900 < x < 1500:
            y = HZ - 25 - 10 * math.sin(x / 50.0)
        pts.append((x, y))
    pts.append((S, HZ))
    paste_fill(img, poly_mask(pts), hexc("#c08a8f", 200))
    pts = [(0, HZ)]
    for x in range(0, S + 1, 48):
        y = HZ - 30 - 26 * math.sin(x / 140.0 + 0.6)
        if 820 < x < 1650:
            y = HZ - 8
        pts.append((x, y))
    pts.append((S, HZ))
    paste_fill(img, poly_mask(pts), hexc("#9c6f80", 220))


def sea(img, sun_x):
    g = vgrad(S, S - HZ, [(0, "#5fb3ad"), (0.35, TEAL), (1.0, "#15475a")])
    img.paste(g, (0, HZ))
    d = ImageDraw.Draw(img)
    # glitter path below the sun, widening toward the viewer
    for i in range(420):
        t = rng.random() ** 1.6
        y = HZ + 6 + t * (S - HZ - 120)
        half = 30 + t * 360
        x = sun_x + rng.uniform(-half, half) * (0.4 + 0.6 * rng.random())
        L = 14 + t * 110 * rng.random()
        th = 2 + t * 7
        a = int(255 * (1 - 0.55 * t))
        col = SUN if rng.random() < 0.7 else PEACH
        d.rounded_rectangle([x - L / 2, y, x + L / 2, y + th], radius=th / 2, fill=hexc(col, a))
    # soft horizontal ripple lines across the bay
    for i in range(140):
        y = HZ + 20 + (rng.random() ** 1.3) * (S - HZ - 60)
        x = rng.uniform(-100, S)
        L = rng.uniform(40, 260)
        d.line([x, y, x + L, y], fill=hexc("#8fd0c7", 70), width=3)


def whale_outline():
    """Silhouette of the sleeping stone whale island (head left, back, tail dives right)."""
    pts = []
    pts += bezier((250, HZ + 20), (205, 1020), (300, 760), (560, 700))      # head front
    pts += bezier((560, 700), (800, 650), (1060, 700), (1250, 820))           # crown of the back
    pts += bezier((1250, 820), (1400, 900), (1520, 1040), (1610, HZ + 20))     # back slopes into sea
    pts += [(1610, HZ + 40), (250, HZ + 40)]
    return pts


def tail_outline():
    pts = []
    dx = 20
    pts += bezier((1690, HZ + 30), (1720, 1150), (1735, 1060), (1760, 990))
    pts += bezier((1760, 990), (1700, 930), (1640, 880), (1600, 800))        # left fluke
    pts += bezier((1600, 800), (1700, 850), (1770, 900), (1800, 945))
    pts += bezier((1800, 945), (1840, 880), (1900, 830), (1990, 790))        # right fluke
    pts += bezier((1990, 790), (1950, 880), (1880, 960), (1830, 1000))
    pts += bezier((1830, 1000), (1850, 1080), (1860, 1160), (1880, HZ + 30))
    return [(x + dx, y) for x, y in pts]


def island(img):
    body = whale_outline()
    m = poly_mask(body)
    # stone body: gradient from sun-lit apricot rim (right/top) to deep teal stone
    shade = vgrad(S, S, [(0.0, STONE), (0.42, STONE), (0.62, DEEP), (1.0, NAVY)])
    paste_fill(img, m, shade)
    # rim light on the sun side: offset mask difference
    off = ImageChops.offset(m, -16, 14)
    rim = ImageChops.subtract(m, off)
    rim = rim.filter(ImageFilter.GaussianBlur(3))
    paste_fill(img, rim, hexc(STONE_LIT))
    # belly grooves of the whale (the rorqual pleats) near the waterline at the head
    d = ImageDraw.Draw(img)
    for k in range(6):
        y0 = 1150 + k * 18
        d.line(bezier((290, y0), (420, y0 + 20), (620, y0 + 14), (820, y0 - 10), 30),
               fill=hexc("#1a3346", 200), width=6)
    # mouth line
    d.line(bezier((262, 1080), (380, 1110), (560, 1110), (700, 1070), 40), fill=hexc(NAVY), width=10)
    # tail fluke rock with lit rim
    tm = poly_mask(tail_outline())
    paste_fill(img, tm, shade)
    trim = ImageChops.subtract(tm, ImageChops.offset(tm, -14, 12)).filter(ImageFilter.GaussianBlur(3))
    paste_fill(img, trim, hexc(STONE_LIT))
    return m


def eye_grotto(img):
    d = ImageDraw.Draw(img)
    cx, cy = 470, 1000
    glow = Image.new("L", (S, S), 0)
    ImageDraw.Draw(glow).ellipse([cx - 120, cy - 120, cx + 120, cy + 120], fill=150)
    glow = glow.filter(ImageFilter.GaussianBlur(40))
    paste_fill(img, glow, hexc("#ffcf7a"))
    d.ellipse([cx - 52, cy - 46, cx + 52, cy + 46], fill=hexc("#ffd98e"), outline=hexc(CREAM), width=8)
    d.arc([cx - 70, cy - 72, cx + 70, cy + 40], 200, 340, fill=hexc(NAVY), width=10)  # sleepy lid
    # little arched window mullions
    d.line([cx, cy - 46, cx, cy + 46], fill=hexc("#b8693f"), width=6)
    d.line([cx - 52, cy, cx + 52, cy], fill=hexc("#b8693f"), width=6)


def house(d, x, y, w, h, roof=TERRA, lit=True):
    # wall with shaded side
    d.rectangle([x, y, x + w, y + h], fill=hexc(CREAM))
    d.rectangle([x + w * 0.62, y, x + w, y + h], fill=hexc("#e8c9a6"))
    # roof: low hip
    d.polygon([(x - 6, y), (x + w / 2, y - h * 0.42), (x + w + 6, y)], fill=hexc(roof))
    d.line([(x + w / 2, y - h * 0.42), (x + w + 6, y)], fill=hexc("#9e4229"), width=3)
    if lit:
        ww = max(5, w * 0.16)
        d.rectangle([x + w * 0.2, y + h * 0.35, x + w * 0.2 + ww, y + h * 0.35 + ww * 1.5],
                    fill=hexc("#ffcd6b"))
        if w > 46:
            d.rectangle([x + w * 0.66, y + h * 0.35, x + w * 0.66 + ww, y + h * 0.35 + ww * 1.5],
                        fill=hexc("#f5b24f"))


def village(img, body_mask):
    """Terraced white town climbing the whale's back, clipped to the island."""
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # terrace walls following the back
    for row in range(7):
        y_off = 70 + row * 62
        pts = bezier((560, 700 + y_off), (800, 650 + y_off), (1060, 700 + y_off), (1250, 820 + y_off), 50)
        d.line(pts, fill=hexc("#d9b48c", 255), width=10)
    rr = random.Random(11)
    for row in range(7):
        y_off = 70 + row * 62
        curve = bezier((560, 700 + y_off), (800, 650 + y_off), (1060, 700 + y_off), (1250, 820 + y_off), 200)
        x = 600 + rr.randint(0, 90)
        while x < 1380:
            # find y on this terrace curve at x
            y = min(curve, key=lambda p: abs(p[0] - x))[1]
            w = rr.randint(30, 74)
            h = rr.randint(26, 56)
            if rr.random() < 0.18:
                x += rr.randint(30, 70)        # gaps: gardens and lanes
                continue
            if rr.random() < 0.80:
                roof = TERRA if rr.random() < 0.75 else CORAL
                house(d, x, y - h - 4, w, h, roof=roof)
            else:
                # lemon tree
                r = rr.randint(14, 20)
                d.ellipse([x, y - 2 * r - 6, x + 2 * r, y - 6], fill=hexc(LEAF))
                for _ in range(4):
                    fx = x + rr.randint(4, 2 * r - 6)
                    fy = y - rr.randint(10, 2 * r)
                    d.ellipse([fx, fy, fx + 7, fy + 7], fill=hexc("#f4d03f"))
            x += w + rr.randint(8, 30)
    # zig-zag stairway down to the harbour
    sx, sy = 1180, 860
    for k in range(9):
        nx = sx + (-60 if k % 2 else 60)
        ny = sy + 42
        d.line([sx, sy, nx, ny], fill=hexc(CREAM, 230), width=7)
        sx, sy = nx, ny
    clip = ImageChops.multiply(layer.getchannel("A"), body_mask)
    img.paste(layer, (0, 0), clip)
    # harbour quay on the water at the island's foot
    dd = ImageDraw.Draw(img)
    dd.rectangle([1080, HZ - 14, 1560, HZ + 10], fill=hexc("#d9b48c"))
    dd.rectangle([1080, HZ + 10, 1560, HZ + 22], fill=hexc("#8d5a43"))
    for k in range(7):
        x = 1100 + k * 66
        dd.line([x, HZ - 14, x, HZ - 60], fill=hexc("#3b2c2a"), width=4)
        dd.ellipse([x - 9, HZ - 74, x + 9, HZ - 56], fill=hexc("#ffcf6e"))


def lighthouse(img):
    """Slender white lighthouse on the whale's crown, where its spout would be."""
    d = ImageDraw.Draw(img)
    bx, by = 640, 705   # base on the crown
    top = 545
    wb, wt = 46, 30
    # beam fan
    beam = Image.new("L", (S, S), 0)
    bd = ImageDraw.Draw(beam)
    bd.polygon([(bx, top + 20), (bx - 900, top - 210), (bx - 900, top + 40)], fill=70)
    bd.polygon([(bx, top + 20), (bx + 1100, top - 120), (bx + 1100, top + 90)], fill=55)
    beam = beam.filter(ImageFilter.GaussianBlur(18))
    paste_fill(img, beam, hexc("#fff4d6"))
    # tower body with red bands
    d.polygon([(bx - wb, by), (bx - wt, top + 60), (bx + wt, top + 60), (bx + wb, by)], fill=hexc(CREAM))
    d.polygon([(bx + 8, by), (bx + 6, top + 60), (bx + wt, top + 60), (bx + wb, by)], fill=hexc("#e6cfae"))
    span = by - top - 60
    for fa, fb in [(0.22, 0.36), (0.58, 0.72)]:
        y0, y1 = top + 60 + fa * span, top + 60 + fb * span
        f0, f1 = fa, fb
        w0 = wt + (wb - wt) * f0
        w1 = wt + (wb - wt) * f1
        d.polygon([(bx - w0, y0), (bx + w0, y0), (bx + w1, y1), (bx - w1, y1)], fill=hexc(CORAL))
    # gallery, lantern room and cap
    d.rectangle([bx - 44, top + 48, bx + 44, top + 62], fill=hexc(NAVY))
    glow = Image.new("L", (S, S), 0)
    ImageDraw.Draw(glow).ellipse([bx - 110, top - 80, bx + 110, top + 130], fill=200)
    glow = glow.filter(ImageFilter.GaussianBlur(36))
    paste_fill(img, glow, hexc("#fff0b0"))
    d.rectangle([bx - 26, top, bx + 26, top + 48], fill=hexc("#fff3b8"))
    d.line([bx, top, bx, top + 48], fill=hexc("#d48a3a"), width=4)
    d.polygon([(bx - 36, top), (bx, top - 46), (bx + 36, top)], fill=hexc(TERRA))
    d.ellipse([bx - 7, top - 58, bx + 7, top - 44], fill=hexc(NAVY))


def reflection(img, body_mask):
    """Mirror the island into the bay, darkened and broken by ripples."""
    top = img.crop((0, 0, S, HZ + 20))
    flip = top.transpose(Image.FLIP_TOP_BOTTOM)
    m = body_mask.crop((0, 0, S, HZ + 20)).transpose(Image.FLIP_TOP_BOTTOM)
    rip = Image.new("L", flip.size, 0)
    rd = ImageDraw.Draw(rip)
    y = 0
    rr = random.Random(5)
    while y < flip.size[1]:
        h = 6 + y * 0.03
        rd.rectangle([0, y, S, y + h], fill=95 - min(80, int(y * 0.10)))
        y += h + 4 + y * 0.02 + rr.random() * 6
    m = ImageChops.multiply(m, rip)
    tint = Image.new("RGBA", flip.size, hexc("#163f52"))
    refl = Image.blend(flip, tint, 0.55)
    img.paste(refl, (0, HZ + 18), m)


def boats(img):
    d = ImageDraw.Draw(img)

    def sail(x, y, s, flip=False):
        sgn = -1 if flip else 1
        d.polygon([(x - 34 * s, y), (x + 34 * s, y), (x + 24 * s, y + 14 * s), (x - 26 * s, y + 14 * s)],
                  fill=hexc(NAVY))
        d.line([x, y, x, y - 92 * s], fill=hexc(NAVY), width=max(2, int(3 * s)))
        d.polygon([(x + 3 * sgn, y - 88 * s), (x + 3 * sgn, y - 6 * s), (x + 54 * s * sgn, y - 6 * s)],
                  fill=hexc(CREAM))
        d.polygon([(x - 3 * sgn, y - 70 * s), (x - 3 * sgn, y - 8 * s), (x - 30 * s * sgn, y - 8 * s)],
                  fill=hexc("#f0d9b5"))
        d.line([x - 60 * s, y + 18 * s, x + 60 * s, y + 18 * s], fill=hexc(SUN, 160), width=3)

    sail(1080, 1430, 1.15)
    sail(1530, 1350, 0.8, flip=True)
    sail(820, 1330, 0.6)
    sail(1900, 1520, 1.0, flip=True)
    # little ferry heading for the harbour
    fx, fy = 1340, 1500
    d.polygon([(fx - 110, fy), (fx + 120, fy), (fx + 96, fy + 34), (fx - 92, fy + 34)], fill=hexc(NAVY))
    d.rectangle([fx - 70, fy - 46, fx + 60, fy], fill=hexc(CREAM))
    d.rectangle([fx - 70, fy - 46, fx + 60, fy - 36], fill=hexc(CORAL))
    for k in range(5):
        d.rectangle([fx - 58 + k * 24, fy - 30, fx - 46 + k * 24, fy - 16], fill=hexc("#ffcd6b"))
    d.rectangle([fx + 10, fy - 90, fx + 34, fy - 46], fill=hexc(CORAL))
    for k, r in enumerate([20, 28, 36]):
        d.ellipse([fx + 30 + k * 40 - r, fy - 130 - k * 26 - r, fx + 30 + k * 40 + r, fy - 130 - k * 26 + r],
                  fill=hexc(CREAM, 150 - k * 35))
    d.line([fx - 160, fy + 40, fx + 170, fy + 40], fill=hexc(SUN, 170), width=4)


def foreground(img):
    """Sunny terrace: a cream balustrade along the bottom and bougainvillea framing both corners."""
    d = ImageDraw.Draw(img)
    rail_y = 1780
    d.rectangle([0, rail_y, S, rail_y + 34], fill=hexc("#f1dcc0"))
    d.rectangle([0, rail_y + 34, S, rail_y + 46], fill=hexc("#c9a582"))
    for x in range(20, S, 86):
        d.ellipse([x + 6, rail_y + 60, x + 50, rail_y + 130], fill=hexc("#ead2b2"))
        d.rectangle([x + 16, rail_y + 46, x + 40, S], fill=hexc("#ead2b2"))
        d.rectangle([x + 30, rail_y + 46, x + 40, S], fill=hexc("#cfae8b"))
    d.rectangle([0, 1960, S, S], fill=hexc("#d8b892"))
    rr = random.Random(3)

    def bloom(cx, cy, rx, ry, n):
        for _ in range(n):
            a = rr.uniform(0, 2 * math.pi)
            r = rr.random() ** 0.6
            x = cx + math.cos(a) * rx * r
            y = cy + math.sin(a) * ry * r
            s = rr.randint(22, 46)
            col = LEAF if rr.random() < 0.38 else rr.choice([BOUG, "#e8679a", "#c43b6e", "#f08bb0"])
            d.ellipse([x - s, y - s * 0.8, x + s, y + s * 0.8], fill=hexc(col))

    # left vine climbing the frame edge, right corner bush
    bloom(70, 1650, 210, 380, 420)
    bloom(240, 1900, 300, 160, 260)
    bloom(1990, 1820, 230, 260, 340)
    bloom(1860, 1980, 260, 110, 160)
    # a few branches reaching in
    d.line(bezier((0, 1300), (120, 1340), (200, 1420), (250, 1560), 30), fill=hexc("#5a3b2c"), width=10)
    bloom(150, 1350, 120, 80, 120)


def title(img):
    d = ImageDraw.Draw(img)
    big = ImageFont.truetype(FONTS + "BOD_BLAR.TTF", 330)
    small = ImageFont.truetype(FONTS + "BOD_R.TTF", 74)
    word = "BALENNE"
    track = 22
    widths = [d.textlength(ch, font=big) for ch in word]
    total = sum(widths) + track * (len(word) - 1)
    x = (S - total) / 2
    y = 70
    # shadow then letters
    for dx, dy, col in [(10, 12, hexc("#16263a", 200)), (0, 0, hexc(CREAM))]:
        xx = x
        for ch, w in zip(word, widths):
            d.text((xx + dx, y + dy), ch, font=big, fill=col)
            xx += w + track
    sub = "ISLE  OF  THE  SLEEPING  WHALE"
    sw = d.textlength(sub, font=small)
    sy = y + 370
    d.line([S / 2 - sw / 2 - 160, sy + 44, S / 2 - sw / 2 - 40, sy + 44], fill=hexc(CREAM), width=5)
    d.line([S / 2 + sw / 2 + 40, sy + 44, S / 2 + sw / 2 + 160, sy + 44], fill=hexc(CREAM), width=5)
    d.text(((S - sw) / 2, sy), sub, font=small, fill=hexc(CREAM))


def finish(img):
    """Lithograph feel: paper grain, gentle vignette, cream border."""
    arr = np.asarray(img.convert("RGB")).astype(np.float32)
    gen = np.random.default_rng(42)
    grain = gen.normal(0, 7.5, (S, S, 1))
    arr = arr + grain
    yy, xx = np.mgrid[0:S, 0:S]
    r = np.sqrt(((xx - S / 2) / (S / 2)) ** 2 + ((yy - S / 2) / (S / 2)) ** 2)
    arr *= (1 - 0.16 * np.clip(r - 0.55, 0, 1) ** 1.5)[:, :, None]
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(out)
    d.rectangle([0, 0, S - 1, S - 1], outline=hexc(CREAM)[:3], width=34)
    d.rectangle([44, 44, S - 45, S - 45], outline=hexc(NAVY)[:3], width=6)
    return out


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "poster.png"
    img = Image.new("RGBA", (S, S), hexc(NAVY))
    sky(img)
    sun_x = sun(img)
    mountains(img)
    sea(img, sun_x)
    body = island(img)
    village(img, body)
    eye_grotto(img)
    lighthouse(img)
    reflection(img, body)
    boats(img)
    foreground(img)
    title(img)
    final = finish(img).resize((OUT, OUT), Image.LANCZOS)
    # the gate caps the file at 1 MiB: grainy art compresses far better as a high-quality JPEG
    final.save(out_path, "JPEG", quality=93, subsampling=0, optimize=True)
    print(out_path, final.size)


if __name__ == "__main__":
    main()
