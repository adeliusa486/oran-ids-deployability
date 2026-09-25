"""Extract the pictograms of the Figure 2 render (figures/source/fig2_candidate_a.jpg).

The icons are kept exactly as drawn. Only the background around each icon is
removed: pixels connected to the crop border and close to the local background
colour become transparent, so an icon can sit on any panel fill while its own
interior fills are kept. All wording is set in LaTeX (paper/fig2_pipeline.tex).

Usage (repo root):  python scripts/extract_figure2_icons.py
Output: figures/icons/f2_*.png and figures/icons/_contact_f2.png
"""
from __future__ import annotations

import pathlib

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

SRC = Image.open("figures/source/fig2_candidate_a.jpg").convert("RGB")
OUT = pathlib.Path("figures/icons")
OUT.mkdir(parents=True, exist_ok=True)

# name -> (left, top, right, bottom) in ORIGINAL pixels (2752 x 1536),
# read from 1:1 gridded crops of the render.
BOXES = {
    "tower":    (195, 315, 272, 380),
    "database": (135, 598, 195, 660),
    "flowdoc":  (196, 970, 275, 1040),
    "grid":     (426, 618, 508, 702),
    "splits":   (718, 652, 797, 738),
    "bars":     (1176, 590, 1226, 636),
    "tree":     (1086, 1140, 1144, 1194),
    "forest":   (1084, 1200, 1154, 1250),
    "mlp":      (1106, 1350, 1174, 1418),
    "scatter":  (1795, 288, 1893, 378),
    "range":    (1982, 596, 2014, 708),
    "dbsmall":  (1964, 918, 2012, 980),
    "bell":     (1948, 1106, 2016, 1178),
    "watch":    (2146, 646, 2190, 694),
}


def cutout(im: Image.Image, tol: float = 22.0, pad: int = 3) -> Image.Image:
    """Make the border-connected background transparent and trim to content."""
    a = np.asarray(im).astype(float)
    edge = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    bg = np.median(edge, axis=0)
    near = np.linalg.norm(a - bg, axis=2) < tol
    lab, _ = ndimage.label(near)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
    border.discard(0)
    bgmask = np.isin(lab, list(border))
    alpha = np.where(bgmask, 0, 255).astype(np.uint8)
    rgba = np.dstack([a.astype(np.uint8), alpha])
    ys, xs = np.nonzero(alpha)
    t, b = max(0, ys.min() - pad), min(a.shape[0], ys.max() + pad + 1)
    l, r = max(0, xs.min() - pad), min(a.shape[1], xs.max() + pad + 1)
    return Image.fromarray(rgba[t:b, l:r], "RGBA")


tiles = []
for name, box in BOXES.items():
    ic = cutout(SRC.crop(box))
    ic = ic.resize((ic.width * 3, ic.height * 3), Image.LANCZOS)
    ic.save(OUT / f"f2_{name}.png")
    tiles.append((name, ic))

cols = 7
tw = max(c.width for _, c in tiles)
th = max(c.height for _, c in tiles)
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (cols * (tw + 14), rows * (th + 30)), (205, 222, 226))
d = ImageDraw.Draw(sheet)
for i, (name, c) in enumerate(tiles):
    r, col = divmod(i, cols)
    x = col * (tw + 14) + 7 + (tw - c.width) // 2
    y = r * (th + 30) + 4 + (th - c.height) // 2
    sheet.paste(c, (x, y), c)
    d.text((col * (tw + 14) + 7, r * (th + 30) + th + 8), name, fill="black")
sheet.save(OUT / "_contact_f2.png")
print("extracted %d icons" % len(tiles))
