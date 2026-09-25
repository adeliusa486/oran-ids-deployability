"""Extract the pictograms of the Figure 1 render (figures/source/fig1_arch_raw_v2.jpg).

The icons are kept exactly as drawn. Only the background around each icon is
removed: pixels connected to the crop border and close to the local background
colour become transparent, so an icon can sit on any panel fill while its own
interior fills are kept. All wording is set in LaTeX (paper/fig1_architecture.tex).

Usage (repo root):  python scripts/extract_figure1_icons.py
Output: figures/icons/f1_*.png and figures/icons/_contact_f1.png
"""
from __future__ import annotations

import pathlib

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

SRC = Image.open("figures/source/fig1_arch_raw_v2.jpg").convert("RGB")
OUT = pathlib.Path("figures/icons")
OUT.mkdir(parents=True, exist_ok=True)

# name -> (left, top, right, bottom) in ORIGINAL pixels (2752 x 1536),
# read from 1:1 gridded crops of the render.
BOXES = {
    "camera":   (105, 362, 212, 458),
    "meter":    (288, 358, 388, 458),
    "watch":    (122, 566, 190, 672),
    "vehicle":  (88, 772, 224, 864),
    "robot":    (108, 1002, 220, 1108),
    "plc":      (328, 1064, 440, 1146),
    "gateway":  (345, 727, 458, 842),
    "antenna":  (780, 288, 874, 400),
    "kpichart": (1884, 458, 1962, 548),
    "windows":  (2060, 396, 2172, 472),
    "table":    (2042, 760, 2184, 862),
    "exporter": (1722, 1044, 1804, 1124),
    "flowdoc":  (1910, 1040, 1982, 1124),
    "featvec":  (2072, 1044, 2156, 1124),
    "bell":     (2312, 769, 2392, 850),
    "lock":     (2553, 468, 2627, 542),
    "isolate":  (2553, 608, 2627, 682),
    "scales":   (2543, 757, 2633, 818),
    "reroute":  (2543, 912, 2637, 968),
    "mitig":    (2543, 1068, 2642, 1162),
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
    ic.save(OUT / f"f1_{name}.png")
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
sheet.save(OUT / "_contact_f1.png")
print("extracted %d icons" % len(tiles))
