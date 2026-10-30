#!/usr/bin/python3
"""Generate the MyProjects app icon (dark rounded square + clipboard + check).

Requires Pillow: python3 -m pip install pillow
Writes PNGs to ~/.local/share/icons/hicolor/<size>x<size>/apps/myprojects.png
"""
from PIL import Image, ImageDraw
import os

OUT = os.path.expanduser("~/.local/share/icons/hicolor")
SIZE = 512

BG    = "#1e1e2e"
BOARD = "#cdd6f4"
CLIP  = "#89b4fa"
CHECK = "#89b4fa"
BAR   = "#7f849c"

S = SIZE
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)


def rr(box, r, fill):
    d.rounded_rectangle(box, radius=r, fill=fill)


# background rounded square
rr((16, 16, S - 16, S - 16), 96, BG)
# clipboard body + clip
rr((184, 168, 328, 344), 20, BOARD)
rr((232, 136, 280, 184), 12, CLIP)
# one check + two pending bars
d.line([(212, 208), (238, 234), (300, 176)], fill=CHECK, width=12,
       joint="curve")
bar_r = 4
rr((208, 252 - bar_r, 304, 252 + bar_r), bar_r, BAR)
rr((208, 300 - bar_r, 304, 300 + bar_r), bar_r, BAR)

img.save(os.path.join(OUT, "512x512", "apps", "myprojects.png"))

for s in (256, 128, 64, 48):
    sub = img.resize((s, s), Image.LANCZOS)
    dstdir = os.path.join(OUT, f"{s}x{s}", "apps")
    os.makedirs(dstdir, exist_ok=True)
    sub.save(os.path.join(dstdir, "myprojects.png"))

print("icons written to", OUT)
