"""Extract the pictograms from the source renders, trimmed and text-free.

The icons are kept exactly as drawn; only surrounding whitespace and any
neighbouring glyphs are cropped away. All wording is re-set in LaTeX so the
figure text is selectable and matches the body font.
"""
from PIL import Image, ImageChops, ImageDraw
import pathlib

SRC1 = Image.open("figures/source/fig1_arch_raw.jpeg").convert("RGB")
# The two style references supplied for the restyle. Only pictograms are
# taken from them -- their content belongs to a different paper.
SREF = Image.open("figures/source/style_ref_1.jpg").convert("RGB")
OUT = pathlib.Path("figures/icons")
OUT.mkdir(parents=True, exist_ok=True)

# name -> (left, top, right, bottom) in ORIGINAL pixels of fig1
BOXES = {
    # IoT population
    "camera":      (70, 552, 165, 628),
    "thermo":      (248, 548, 302, 632),
    "indsensor":   (466, 570, 524, 678),
    "meter":       (68, 712, 150, 790),
    "watch":       (76, 850, 143, 930),
    "vehicle":     (220, 846, 314, 914),
    "robot":       (64, 990, 154, 1070),
    "plc":         (138, 1120, 238, 1194),
    "gateway":     (320, 1128, 404, 1198),
    # access point (router + antenna)
    "ap":          (434, 846, 512, 926),
    # RAN nodes
    "oru":         (608, 858, 700, 952),
    "odu":         (778, 858, 856, 952),
    "ocu":         (974, 858, 1052, 952),
    # telemetry pipeline, packet lane
    "packet":      (1752, 610, 1826, 662),
    "flowrec":     (1876, 602, 1938, 672),
    "featvec":     (1986, 606, 2050, 664),
    # telemetry pipeline, radio lane
    "e2sm":        (1754, 982, 1830, 1042),
    "kpirec":      (1876, 980, 1938, 1050),
    "tsmatrix":    (1990, 980, 2060, 1050),
    # harmonised feature space
    "database":    (2138, 852, 2228, 918),
    # closed-loop actions
    "act_alert":   (2658, 644, 2712, 694),
    "act_block":   (2658, 720, 2706, 772),
    "act_isolate": (2658, 800, 2706, 850),
    "act_policy":  (2658, 872, 2710, 926),
    "act_reroute": (2676, 952, 2718, 1008),
    "act_mitig":   (2662, 1068, 2718, 1110),
}

# name -> box in ORIGINAL pixels of style_ref_1.jpg
REF_BOXES = {
    "ic_warn": (2556, 898, 2615, 953),
}


def trim(im, thresh=246, pad=3):
    """Drop uniform near-white margin so each icon sits tight in its box."""
    g = im.convert("L").point(lambda v: 0 if v < thresh else 255)
    bbox = ImageChops.invert(g).getbbox()
    if bbox is None:
        return im
    l, t, r, b = bbox
    l, t = max(0, l - pad), max(0, t - pad)
    r, b = min(im.width, r + pad), min(im.height, b + pad)
    return im.crop((l, t, r, b))


tiles = []
for src, boxes in ((SRC1, BOXES), (SREF, REF_BOXES)):
    for name, box in boxes.items():
        ic = trim(src.crop(box))
        # upscale modestly so the icon stays crisp at print size
        ic = ic.resize((ic.width * 2, ic.height * 2), Image.LANCZOS)
        ic.save(OUT / f"{name}.png")
        tiles.append((name, ic))

cols = 7
tw = max(c.width for _, c in tiles)
th = max(c.height for _, c in tiles)
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (cols * (tw + 14), rows * (th + 30)), "white")
d = ImageDraw.Draw(sheet)
for i, (name, c) in enumerate(tiles):
    r, col = divmod(i, cols)
    x = col * (tw + 14) + 7 + (tw - c.width) // 2
    y = r * (th + 30) + 4 + (th - c.height) // 2
    sheet.paste(c, (x, y))
    d.text((col * (tw + 14) + 7, r * (th + 30) + th + 8), name, fill="black")
sheet.save(OUT / "_contact.png")
print("extracted %d icons" % len(tiles))
