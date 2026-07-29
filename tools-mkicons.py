#!/usr/bin/env python3
"""Generate BREW PWA icons from the app's own 18x20 pixel-art mug."""
import math, os, struct, zlib

POT = [
    "                  ",
    "                  ",
    "   #..........#   ",
    "   #..........#   ",
    "   #..........#HHH",
    "   #..........#  H",
    "   #..........#  H",
    "   #..........#  H",
    "   #..........#  H",
    "   #..........#  H",
    "   #..........#HHH",
    "   #..........#   ",
    "   #..........#   ",
    "   #..........#   ",
    "    #........#    ",
    "    #........#    ",
    "     #......#     ",
    "     ########     ",
    "      ######      ",
    "                  ",
]
GW, GH = 18, 20
FILL_TOP, FILL_BOT = 2, 16
FILL_ROWS = FILL_BOT - FILL_TOP + 1
BAND_H = FILL_ROWS / 4.0
OUTLINE = (0x5a, 0x3a, 0x22)
FOAM = (0xff, 0xf4, 0xdd)
COLOR = {"B": (0x3a, 0x24, 0x17), "R": (0x6e, 0x43, 0x21),
         "E": (0xcd, 0xa0, 0x66), "W": (0xe7, 0xd2, 0xa6)}
ORDER = ["B", "R", "E", "W"]
BG_TOP, BG_BOT = (0xff, 0xf7, 0xec), (0xed, 0xe0, 0xcb)


def hash01(x, y):
    s = math.sin(x * 12.9898 + y * 78.233) * 43758.5453
    return s - math.floor(s)


def fill_color(x, y):
    """Same band + dither logic the app's canvas uses, for a full (4/4) cup."""
    r_from_bottom = FILL_BOT - y
    bi = min(3, int(r_from_bottom / BAND_H))
    c = COLOR[ORDER[bi]]
    if bi < 3:
        dist = (bi + 1) * BAND_H - r_from_bottom
        if dist < 1.3 and hash01(x, y) < (1 - dist / 1.3):
            c = COLOR[ORDER[bi + 1]]
    return c


def render(size, content_frac):
    cell = max(1, round(size * content_frac / GH))
    ox = (size - GW * cell) // 2
    oy = (size - GH * cell) // 2
    # vertical background gradient
    rows = []
    for y in range(size):
        t = y / max(1, size - 1)
        bg = tuple(round(BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * t) for i in range(3))
        rows.append([bg] * size)
    for gy in range(GH):
        for gx in range(GW):
            ch = POT[gy][gx]
            if ch == " ":
                continue
            if ch in "#H":
                c = OUTLINE
            elif FILL_TOP <= gy <= FILL_BOT:
                c = FOAM if (gx == 8 and gy == FILL_TOP) else fill_color(gx, gy)
            else:
                c = COLOR["W"]
            for dy in range(cell):
                py = oy + gy * cell + dy
                if not (0 <= py < size):
                    continue
                row = rows[py]
                for dx in range(cell):
                    pxx = ox + gx * cell + dx
                    if 0 <= pxx < size:
                        row[pxx] = c
    return rows


def write_png(path, rows):
    size = len(rows)
    raw = b"".join(b"\x00" + b"".join(bytes(p) for p in row) for row in rows)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 9))
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
os.makedirs(out, exist_ok=True)
# purpose "any" / apple-touch-icon: mug fills most of the tile (iOS masks corners itself)
for size in (32, 180, 192, 512):
    n = write_png(os.path.join(out, f"icon-{size}.png"), render(size, 0.78))
    print(f"icon-{size}.png  {n} bytes")
# maskable: extra padding so nothing is cropped by Android's mask
n = write_png(os.path.join(out, "icon-512-maskable.png"), render(512, 0.56))
print(f"icon-512-maskable.png  {n} bytes")
