"""Paper figure: the Voiager 5 tyre sidewall size codes, from the author's photographs.

Front: tyre-images/IMG_8175.jpeg (60/55-8.5); rear: tyre-images/rear.jpeg (60/55-7.5, photo
taken upside down, rotated here). Photographed on a parked Voi Voiager 5 in Oxford on
2026-10-09. Nominal outer diameter = rim + 2 x width x aspect ratio:
  front 8.5 x 25.4 + 2 x 60 x 0.55 = 282 mm (11.1 in); rear 7.5 x 25.4 + 66 = 257 mm (10.1 in).
The figure is re-rendered from crops, so no photo metadata (EXIF, location) is carried over.

Usage
    python scripts/tyre_figure.py      -> paper/figures/fig_tyres.png
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageOps

SRC = Path("tyre-images")
OUT = Path("paper/figures/fig_tyres.png")
INK, MUTED = "#222222", "#6b6b6b"


def nominal_od_mm(width_mm, aspect_pct, rim_in):
    return rim_in * 25.4 + 2 * width_mm * aspect_pct / 100


def main():
    # (photo, crop box in the upright image, rotation in degrees, title)
    front = ImageOps.exif_transpose(Image.open(SRC / "IMG_8175.jpeg"))
    front = front.crop((150, 60, 400, 520)).rotate(90, expand=True)
    rear = ImageOps.exif_transpose(Image.open(SRC / "rear.jpeg"))
    rear = rear.crop((1000, 950, 3400, 1800)).rotate(180)
    panels = [(front, "Front tyre: 60/55-8.5", nominal_od_mm(60, 55, 8.5)),
              (rear, "Rear tyre: 60/55-7.5", nominal_od_mm(60, 55, 7.5))]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.3),
                             gridspec_kw={"width_ratios": [p[0].width / p[0].height for p in panels]})
    for ax, (img, title, od) in zip(axes, panels):
        ax.imshow(img)
        ax.set_title(f"{title}  →  {int(od + 0.5)} mm ≈ {od / 25.4:.1f} in", fontsize=8.5, color=INK,
                     loc="left")
        ax.axis("off")
    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=250, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
