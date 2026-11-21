#!/usr/bin/env python3
"""World news front page for Saturday 21 November 2026.

Pure-stdlib Python 3.13 program. Draws a 1024x1024 newspaper front page
summarising the day's world news and writes it to /output/entry.png
(or $MAKEFUN_OUTPUT_DIR/entry.png). Deterministic: two runs produce
identical bytes. No network, no third-party packages.

Stories (all first reported or happening on 21 November 2026):
  1. Russian missiles land in Poland; NATO chief Rutte to Warsaw.
  2. COP31 climate talks in Antalya spill into overtime.
  3. Russian barrage on Ukraine kills 2, injures 42 in Kryvyi Rih.
  4. JPMorgan, Visa and Mastercard confirm customer-data breach.
  5. Cyclone Akvan's rains lash Odisha a day after landfall.
  6. India fight back in the Wellington Test against New Zealand.
"""

import os
import struct
import zlib

W, H = 1024, 1024

# --- palette ---------------------------------------------------------------
PAPER = (246, 241, 227)
INK = (20, 20, 20)
NAVY = (23, 54, 93)
NAVY_DARK = (16, 38, 66)
RED = (180, 35, 24)
GOLD = (201, 162, 39)
GREY = (90, 90, 90)
LIGHT_GREY = (220, 214, 196)
SKY = (38, 64, 110)
SKY_LIGHT = (96, 130, 178)
GREEN = (46, 125, 50)
GREEN_DARK = (27, 94, 32)
ORANGE = (230, 126, 34)
YELLOW = (244, 196, 48)
WHITE = (255, 255, 255)
BLUE = (30, 90, 168)
CYAN = (120, 200, 220)

# --- canvas ----------------------------------------------------------------
pixels = bytearray(W * H * 3)


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        pixels[i], pixels[i + 1], pixels[i + 2] = c


def rect(x, y, w, h, c):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        for xx in range(x1 - x0):
            i = base + xx * 3
            pixels[i], pixels[i + 1], pixels[i + 2] = c


def hline(x0, x1, y, c):
    for x in range(x0, x1 + 1):
        px(x, y, c)


def vline(x, y0, y1, c):
    for y in range(y0, y1 + 1):
        px(x, y, c)


def line(x0, y0, x1, y1, c):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        px(x0, y0, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def thick_line(x0, y0, x1, y1, c, t=2):
    for ox in range(-t // 2, t // 2 + 1):
        for oy in range(-t // 2, t // 2 + 1):
            line(x0 + ox, y0 + oy, x1 + ox, y1 + oy, c)


def circle(cx, cy, r, c, fill=True):
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            d = (x - cx) ** 2 + (y - cy) ** 2
            if fill:
                if d <= r * r:
                    px(x, y, c)
            else:
                if abs(d - r * r) <= r * 2:
                    px(x, y, c)


def disc(cx, cy, r, c):
    circle(cx, cy, r, c, fill=True)


def ring(cx, cy, r, c, t=3):
    for k in range(t):
        circle(cx, cy, r - k, c, fill=False)


def star4(cx, cy, r, c):
    # four-point compass star
    for i in range(-r, r + 1):
        w = max(1, int((r - abs(i)) * 0.28))
        for x in range(cx - w, cx + w + 1):
            px(x, cy + i, c)
        for y in range(cy - w, cy + w + 1):
            px(cx + i, y, c)


def burst(cx, cy, r, c):
    # explosion starburst: 12 spikes
    import math
    for k in range(12):
        a = k * math.pi / 6
        x1 = int(cx + r * math.cos(a))
        y1 = int(cy + r * math.sin(a))
        thick_line(cx, cy, x1, y1, c, 3)
    disc(cx, cy, int(r * 0.45), c)


# --- 5x7 bitmap font (uppercase only; text is uppercased) ------------------
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
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
}


def text_width(s, scale):
    return len(s) * 6 * scale


def draw_text(x, y, s, scale, c):
    s = s.upper()
    for ch in s:
        glyph = FONT.get(ch, FONT[" "])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":
                    rect(x + col * scale, y + row * scale, scale, scale, c)
        x += 6 * scale


def draw_text_centered(cx, y, s, scale, c):
    draw_text(cx - text_width(s, scale) // 2, y, s, scale, c)


def wrap(s, max_chars):
    words = s.split()
    lines, cur = [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > max_chars:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w) if cur else w
    if cur:
        lines.append(cur)
    return lines


def paragraph(x, y, s, scale, c, max_chars, line_gap=4):
    for ln in wrap(s, max_chars):
        draw_text(x, y, ln, scale, c)
        y += 7 * scale + line_gap
    return y


# --- story visuals ---------------------------------------------------------
def visual_poland(x, y, w, h):
    rect(x, y, w, h, SKY)
    rect(x, y + h - 60, w, 60, (52, 68, 54))  # ground
    # moon
    disc(x + w - 60, y + 42, 20, (235, 230, 200))
    # missile trails: white arcs with orange flame heads
    for (sx, sy, ex, ey) in ((x + 30, y + h - 60, x + 210, y + 40),
                             (x + 150, y + h - 60, x + 330, y + 70),
                             (x + 260, y + h - 60, x + 430, y + 30)):
        mx, my = (sx + ex) // 2, min(sy, ey) - 40
        for t in range(0, 101, 2):
            tt = t / 100.0
            px_ = int((1 - tt) ** 2 * sx + 2 * (1 - tt) * tt * mx + tt * tt * ex)
            py_ = int((1 - tt) ** 2 * sy + 2 * (1 - tt) * tt * my + tt * tt * ey)
            disc(px_, py_, 2, WHITE)
        disc(ex, ey, 7, ORANGE)
        disc(ex, ey, 4, YELLOW)
    # Polish flag on a pole, bottom left
    vline(x + 40, y + h - 130, y + h - 60, (200, 200, 200))
    rect(x + 40, y + h - 130, 84, 18, WHITE)
    rect(x + 40, y + h - 112, 84, 18, RED)
    # NATO compass star in a blue circle, bottom right
    disc(x + w - 70, y + h - 95, 34, (10, 40, 90))
    ring(x + w - 70, y + h - 95, 34, WHITE, 2)
    star4(x + w - 70, y + h - 95, 26, WHITE)
    # jet silhouette
    for dx, dy in ((0, 0), (14, -4), (28, 0)):
        px(x + 300 + dx, y + 150 + dy, WHITE)


def visual_cop31(x, y, w, h):
    rect(x, y, w, h, (198, 226, 238))
    # sun
    disc(x + w - 70, y + 52, 30, YELLOW)
    for k in range(8):
        import math
        a = k * math.pi / 4
        line(x + w - 70 + int(36 * math.cos(a)), y + 52 + int(36 * math.sin(a)),
             x + w - 70 + int(52 * math.cos(a)), y + 52 + int(52 * math.sin(a)), YELLOW)
    # globe
    cx, cy, r = x + 130, y + h // 2 + 6, 62
    disc(cx, cy, r, BLUE)
    disc(cx - 22, cy - 18, 20, GREEN)
    disc(cx + 24, cy + 12, 24, GREEN_DARK)
    disc(cx + 8, cy - 30, 12, GREEN)
    ring(cx, cy, r, NAVY, 2)
    # horizon flags row
    for i, c in enumerate((RED, GOLD, GREEN, BLUE, ORANGE)):
        fx = x + w - 210 + i * 34
        vline(fx, y + h - 34, y + h - 8, INK)
        rect(fx, y + h - 34, 26, 14, c)


def visual_ukraine(x, y, w, h):
    rect(x, y, w, h, (24, 24, 34))
    # damaged buildings
    for bx, bw, bh in ((x + 20, 70, 66), (x + 110, 56, 88), (x + 190, 80, 54),
                       (x + 300, 60, 78), (x + 380, 66, 62)):
        rect(bx, y + h - bh - 20, bw, bh, (58, 58, 70))
        for wy in range(y + h - bh - 8, y + h - 28, 18):
            for wx in range(bx + 8, bx + bw - 8, 16):
                rect(wx, wy, 7, 9, (240, 200, 90))
    # explosion burst over the skyline
    burst(x + 250, y + 62, 46, ORANGE)
    burst(x + 250, y + 62, 26, YELLOW)
    burst(x + 90, y + 44, 22, RED)
    # smoke dots
    for sx, sy, sr in ((x + 250, y + 20, 10), (x + 280, y + 26, 8), (x + 220, y + 18, 8)):
        disc(sx, sy, sr, (120, 120, 120))


def visual_banks(x, y, w, h):
    rect(x, y, w, h, (232, 236, 240))
    # laptop
    rect(x + 40, y + 22, 200, 84, INK)
    rect(x + 48, y + 30, 184, 68, (18, 60, 110))
    # padlock on screen
    rect(x + 118, y + 52, 44, 34, GOLD)
    ring(x + 140, y + 52, 14, GOLD, 4)
    disc(x + 140, y + 66, 6, INK)
    rect(x + 28, y + 106, 224, 8, (120, 120, 120))
    # warning triangle
    for i in range(0, 26):
        hline(x + w - 62 - i, x + w - 62 + i, y + 96 - i, YELLOW)
    draw_text(x + w - 68, y + 62, "!", 2, INK)
    # credit cards
    rect(x + w - 120, y + 24, 84, 34, RED)
    rect(x + w - 120, y + 66, 84, 34, BLUE)
    rect(x + w - 112, y + 34, 30, 8, GOLD)


def visual_cyclone(x, y, w, h):
    rect(x, y, w, h, (196, 216, 230))
    # sea
    rect(x, y + h - 34, w, 34, (24, 90, 140))
    for wx in range(x + 6, x + w - 6, 34):
        line(wx, y + h - 20, wx + 16, y + h - 26, WHITE)
        line(wx + 16, y + h - 26, wx + 32, y + h - 20, WHITE)
    # spiral storm: concentric broken arcs
    import math
    cx, cy = x + w // 2, y + h // 2 - 6
    for r in (18, 30, 42, 54):
        for deg in range(0, 300, 4):
            a = math.radians(deg + r * 3)
            px(int(cx + r * math.cos(a)), int(cy + r * math.sin(a) * 0.8), NAVY)
            px(int(cx + r * math.cos(a)) + 1, int(cy + r * math.sin(a) * 0.8), NAVY)
    disc(cx, cy, 10, RED)
    # rain streaks
    for rx in range(x + 14, x + w - 10, 26):
        line(rx, y + 12, rx - 6, y + 30, (90, 130, 180))
        line(rx, y + h - 62, rx - 6, y + h - 44, (90, 130, 180))


def visual_cricket(x, y, w, h):
    rect(x, y, w, h, (214, 232, 190))
    # pitch
    rect(x + w // 2 - 46, y + 8, 92, h - 16, (222, 200, 150))
    # stumps
    for sx in (x + w // 2 - 18, x + w // 2 - 2, x + w // 2 + 14):
        vline(sx, y + 14, y + 44, YELLOW)
    rect(x + w // 2 - 18, y + 12, 48, 4, YELLOW)
    # bat
    thick_line(x + 60, y + h - 26, x + 96, y + 44, (150, 110, 60), 5)
    rect(x + 88, y + 34, 20, 16, (150, 110, 60))
    # red ball
    disc(x + w - 60, y + 40, 12, RED)
    ring(x + w - 60, y + 40, 12, WHITE, 1)
    # score strip
    rect(x + 16, y + h - 34, w - 32, 24, NAVY)
    draw_text(x + 26, y + h - 28, "159/1", 2, WHITE)


# --- PNG writer (deterministic) --------------------------------------------
def chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def write_png(path):
    raw = b"".join(b"\x00" + pixels[y * W * 3:(y + 1) * W * 3] for y in range(H))
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    data = b"\x89PNG\r\n\x1a\n"
    data += chunk(b"IHDR", ihdr)
    data += chunk(b"IDAT", zlib.compress(raw, 9))
    data += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(data)


# --- page layout -----------------------------------------------------------
def rule(y, c=INK, thickness=2):
    rect(16, y, W - 32, thickness, c)


def main():
    rect(0, 0, W, H, PAPER)

    # masthead
    rect(0, 0, W, 122, NAVY)
    rect(0, 118, W, 4, GOLD)
    draw_text_centered(W // 2, 22, "THE WORLD TODAY", 6, WHITE)
    draw_text_centered(W // 2, 84, "SATURDAY - 21 NOVEMBER 2026", 3, GOLD)

    # ---- lead story: Poland / NATO -------------------------------------
    ly = 140
    visual_poland(16, ly, 500, 280)
    draw_text(532, ly, "NATO ON ALERT", 2, RED)
    y = ly + 34
    for ln in ("RUSSIAN MISSILES", "LAND IN POLAND"):
        draw_text(532, y, ln, 4, INK)
        y += 34
    y += 8
    y = paragraph(532, y,
                  "Two missiles and a drone came down in south-east Poland "
                  "during a huge Russian attack on Ukraine. PM Tusk calls it "
                  "a deliberate provocation. NATO chief Rutte flies to Warsaw "
                  "today. No one was hurt.",
                  2, INK, 39)
    draw_text(532, y + 6, "POLAND - UKRAINE BORDER", 2, GREY)

    rule(448)

    # ---- row B: COP31 and Ukraine --------------------------------------
    by = 464
    draw_text(16, by, "CLIMATE", 2, RED)
    draw_text(528, by, "WAR IN UKRAINE", 2, RED)
    visual_cop31(16, by + 26, 480, 118)
    visual_ukraine(528, by + 26, 480, 118)
    y1 = by + 156
    for ln in ("COP31 TALKS RUN", "INTO OVERTIME"):
        draw_text(16, y1, ln, 3, INK)
        y1 += 26
    paragraph(16, y1 + 4,
              "Fossil fuels cut from the draft as nearly 200 nations haggle "
              "on.",
              2, INK, 40)
    y2 = by + 156
    draw_text(528, y2, "KYIV REGION HIT AGAIN", 3, INK)
    y2 += 26
    draw_text(528, y2, "2 DEAD, 42 HURT", 3, RED)
    paragraph(528, y2 + 30,
              "Russia's overnight barrage hits Kryvyi Rih as the air war "
              "grinds on.",
              2, INK, 40)

    rule(724)

    # ---- row C: banks, cyclone, cricket --------------------------------
    cy = 740
    cols = [
        (16, "MONEY", "BANKS HIT BY", "DATA BREACH", visual_banks,
         "Hackers stole customer data via vendors at JPMorgan, Visa and "
         "Mastercard. Cards safe."),
        (352, "WEATHER", "AKVAN'S RAINS", "LASH INDIA", visual_cyclone,
         "A day after landfall in Odisha, heavy rain floods the coast. "
         "370,000 people were moved to safety."),
        (688, "SPORT", "INDIA FIGHT", "BACK IN WELLINGTON", visual_cricket,
         "India reach 159 for 1 at stumps on day two of the first Test, "
         "trailing New Zealand by 209."),
    ]
    for (cx, kick, h1, h2, vis, body) in cols:
        draw_text(cx, cy, kick, 2, RED)
        vis(cx, cy + 26, 320, 100)
        yy = cy + 136
        draw_text(cx, yy, h1, 2, INK)
        yy += 18
        draw_text(cx, yy, h2, 2, INK)
        paragraph(cx, yy + 22, body, 2, INK, 26, line_gap=2)

    rule(984)
    draw_text_centered(W // 2, 994, "THE WORLD IN ONE PAGE - 21 NOVEMBER 2026", 2, GREY)

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    write_png(os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
