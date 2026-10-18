"""Create a one-slide explanation of original-distribution mass near sampled vectors."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parent
STEM = ROOT / "similarity_mass_slide"

NAVY = "#17324A"
MUTED = "#637486"
TEAL = "#087F7A"
TEAL_LIGHT = "#DDF3EF"
ORANGE = "#DE754A"
ORANGE_LIGHT = "#FCEDE7"
LINE = "#DDE5E9"
BACKGROUND = "#F5F7F8"


def add_panel(fig, x, y, w, h):
    panel = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.008,rounding_size=0.014",
        transform=fig.transFigure,
        linewidth=1,
        edgecolor=LINE,
        facecolor="white",
        zorder=0,
    )
    fig.patches.append(panel)


def add_pptx_with_slide_image(png_path: Path, pptx_path: Path) -> None:
    """Wrap the rendered slide in a standard one-slide OpenXML presentation."""
    width, height = 12192000, 6858000  # 13.333 x 7.5 inches in EMUs
    files = {
        "[Content_Types].xml": f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
</Types>''',
        "_rels/.rels": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>''',
        "ppt/presentation.xml": f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldIdLst><p:sldId id="256" r:id="rId1"/></p:sldIdLst>
  <p:sldSz cx="{width}" cy="{height}" type="screen16x9"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>''',
        "ppt/_rels/presentation.xml.rels": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/>
</Relationships>''',
        "ppt/slides/slide1.xml": f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    <p:pic>
      <p:nvPicPr><p:cNvPr id="2" name="Similarity mass slide"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>
      <p:blipFill><a:blip r:embed="rId1"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
      <p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{width}" cy="{height}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>
    </p:pic>
  </p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>''',
        "ppt/slides/_rels/slide1.xml.rels": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/slide.png"/>
</Relationships>''',
    }
    with ZipFile(pptx_path, "w", ZIP_DEFLATED) as pptx:
        for name, contents in files.items():
            pptx.writestr(name, contents)
        pptx.write(png_path, "ppt/media/slide.png")


def main() -> None:
    rng = np.random.default_rng(12)
    dim = 6
    sampler_mean = np.array([0.4, -0.25, 0.35, 0.0, 0.3, -0.15])
    centers = rng.normal(sampler_mean, 0.6, size=(4, dim))
    check = rng.normal(sampler_mean, 0.6, size=(500, dim))
    original = rng.normal(0, 1, size=(25_000, dim))

    def nearest_distance(vectors):
        distances = np.linalg.norm(vectors[:, None, :] - centers[None, :, :], axis=2)
        return distances.min(axis=1)

    check_distances = nearest_distance(check)
    radius = float(np.quantile(check_distances, 0.9))
    original_distances = nearest_distance(original)
    original_mass = float(np.mean(original_distances <= radius))

    example = centers[2] + np.array([0.10, -0.20, 0.16, 0.08, -0.13, 0.12])
    example_distances = np.linalg.norm(centers - example, axis=1)

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
    })
    fig = plt.figure(figsize=(13.333, 7.5), facecolor=BACKGROUND)

    fig.text(0.045, 0.935, "How much of the original distribution is near the sampled vectors?",
             color=NAVY, fontsize=23, fontweight="bold", va="center")
    fig.text(0.045, 0.885,
             "Measure every original vector's distance to the sample set, then read the shaded histogram area.",
             color=MUTED, fontsize=11.5, va="center")

    panels = [(0.044, 0.223, 0.275, 0.609),
              (0.333, 0.223, 0.263, 0.609),
              (0.610, 0.223, 0.347, 0.609)]
    for box in panels:
        add_panel(fig, *box)

    fig.text(0.064, 0.790, "1   Sample vectors", color=NAVY, fontsize=14, fontweight="bold")
    fig.text(0.064, 0.746, "Each draw has the same 6 features.", color=MUTED, fontsize=10.5)

    vec_ax = fig.add_axes([0.067, 0.307, 0.230, 0.399], zorder=2)
    vec_ax.set_xlim(-0.2, 6.2)
    vec_ax.set_ylim(-0.9, 5.55)
    vec_ax.axis("off")
    values = np.vstack([centers, example])
    labels = [r"$y_1$", r"$y_2$", r"$y_3$", r"$y_4$", r"$x$"]
    color_map = plt.get_cmap("BrBG")
    normalize = TwoSlopeNorm(vmin=-1.5, vcenter=0, vmax=1.5)
    for c in range(dim):
        vec_ax.text(c + 0.48, 5.22, f"f{c+1}", ha="center", va="center", fontsize=9,
                    color=MUTED)
    for row in range(5):
        y = 4.35 - row * 1.05
        if row == 4:
            vec_ax.plot([-0.2, 6.2], [y + 0.71, y + 0.71], color=LINE, lw=1.1)
        vec_ax.text(-0.10, y + 0.35, labels[row], ha="right", va="center",
                    fontsize=12, color=ORANGE if row == 4 else NAVY, fontweight="bold")
        for col in range(dim):
            val = values[row, col]
            cell_color = color_map(normalize(val))
            vec_ax.add_patch(FancyBboxPatch((col + 0.06, y), 0.84, 0.72,
                                            boxstyle="round,pad=0.015,rounding_size=0.08",
                                            facecolor=cell_color,
                                            edgecolor="white", linewidth=1))
            luminance = 0.2126 * cell_color[0] + 0.7152 * cell_color[1] + 0.0722 * cell_color[2]
            vec_ax.text(col + 0.48, y + 0.36, f"{val:+.1f}", ha="center", va="center",
                        color="white" if luminance < 0.51 else NAVY,
                        fontsize=8.0, fontweight="bold")
    fig.text(0.066, 0.264, "Example original vector", color=ORANGE, fontsize=9.4,
             fontweight="bold")

    fig.text(0.353, 0.790, "2   Compute one distance", color=NAVY, fontsize=14,
             fontweight="bold")
    fig.text(0.353, 0.742, "Find the closest sampled vector.", color=MUTED, fontsize=10.5)
    fig.text(0.355, 0.673, r"$D_C(x)=\min_i\,d(x,y_i)$", color=NAVY, fontsize=19)

    bar_ax = fig.add_axes([0.360, 0.360, 0.215, 0.245], zorder=2)
    bar_ax.set_xlim(0, 2.5)
    bar_ax.set_ylim(-0.55, 3.6)
    bar_ax.axis("off")
    nearest_index = int(np.argmin(example_distances))
    for i, distance in enumerate(example_distances):
        yy = 3 - i
        bar_ax.text(-0.06, yy, rf"$y_{i+1}$", ha="right", va="center", fontsize=11,
                    color=NAVY)
        color = TEAL if i == nearest_index else "#C8D4DC"
        bar_ax.barh(yy, distance, height=0.46, color=color, edgecolor="none")
        bar_ax.text(distance + 0.07, yy, f"{distance:.1f}", va="center", fontsize=10,
                    color=TEAL if i == nearest_index else MUTED,
                    fontweight="bold" if i == nearest_index else "normal")
    fig.text(0.354, 0.300, "Small distance = close to a sample", color=TEAL,
             fontsize=10.5, fontweight="bold")
    fig.text(0.354, 0.263, "Use the full vector, not a single feature.",
             color=MUTED, fontsize=9.5)

    fig.text(0.630, 0.790, "3   Read the original mass", color=NAVY,
             fontsize=14, fontweight="bold")
    fig.text(0.630, 0.746, "Histogram distances for original vectors",
             color=MUTED, fontsize=10.5)

    hist_ax = fig.add_axes([0.653, 0.400, 0.277, 0.265], zorder=2)
    bins = np.linspace(0, 5.2, 27)
    counts, edges = np.histogram(original_distances, bins=bins, density=True)
    widths = np.diff(edges)
    hist_ax.bar(edges[:-1], counts, width=widths, align="edge", color="#CDD8DE",
                edgecolor="white", linewidth=0.8)
    for left, right, height in zip(edges[:-1], edges[1:], counts):
        shaded_width = max(0.0, min(right, radius) - left)
        if shaded_width > 0:
            hist_ax.add_patch(Rectangle((left, 0), shaded_width, height,
                                        facecolor=TEAL, edgecolor="none", alpha=0.95))
    hist_ax.axvline(radius, color=ORANGE, lw=2.2, ls=(0, (4, 2)))
    hist_ax.text(radius + 0.08, max(counts) * 0.91, r"$r_{0.90}$", color=ORANGE,
                 fontsize=11, fontweight="bold", ha="left")
    hist_ax.set_xlim(0, 5.2)
    hist_ax.set_ylim(0, max(counts) * 1.16)
    hist_ax.spines[["top", "right", "left"]].set_visible(False)
    hist_ax.spines["bottom"].set_color("#AEBBC4")
    hist_ax.tick_params(axis="x", colors=MUTED, labelsize=9, length=0)
    hist_ax.tick_params(axis="y", left=False, labelleft=False)
    hist_ax.set_xticks([0, 1, 2, 3, 4, 5])
    hist_ax.set_xlabel("Distance to nearest sampled vector", fontsize=9.5,
                       color=MUTED, labelpad=8)

    fig.text(0.636, 0.300, rf"Shaded mass  $A_{{0.90}} \approx {original_mass:.2f}$",
             color=TEAL, fontsize=16, fontweight="bold")
    fig.text(0.636, 0.262, "while covering ~90% of sampler draws", color=MUTED,
             fontsize=10.3)

    bottom = FancyBboxPatch((0.044, 0.051), 0.913, 0.128,
                            boxstyle="round,pad=0.008,rounding_size=0.012",
                            transform=fig.transFigure, linewidth=0,
                            facecolor=NAVY, zorder=0)
    fig.patches.append(bottom)
    fig.text(0.063, 0.135, "Choose the cutoff:", color="#BFE6E1", fontsize=10.5,
             fontweight="bold")
    fig.text(0.063, 0.088,
             r"$r_{\alpha}=\mathrm{quantile}_{\alpha}\{D_C(Y^{\mathrm{check}})\}$",
             color="white", fontsize=13)
    fig.text(0.493, 0.135, "Original probability in that region:",
             color="#BFE6E1", fontsize=10.5, fontweight="bold")
    fig.text(0.493, 0.088,
             r"$A_{\alpha}=P_0[D_C(X)\leq r_{\alpha}]"
             r"=\int_{D_C(z)\leq r_{\alpha}}p_0(z)\,dz$",
             color="white", fontsize=13)

    fig.text(0.953, 0.018, "Illustrative 6D data; α = 0.90",
             ha="right", color=MUTED, fontsize=8.1)

    fig.savefig(STEM.with_suffix(".png"), dpi=200, facecolor=fig.get_facecolor())
    fig.savefig(STEM.with_suffix(".pdf"), facecolor=fig.get_facecolor())
    svg_path = STEM.with_suffix(".svg")
    fig.savefig(svg_path, facecolor=fig.get_facecolor())
    svg_text = svg_path.read_text(encoding="utf-8")
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n",
        encoding="utf-8",
    )
    plt.close(fig)
    add_pptx_with_slide_image(STEM.with_suffix(".png"), STEM.with_suffix(".pptx"))
    print(f"Created slide: r90={radius:.3f}, A90={original_mass:.3f}")


if __name__ == "__main__":
    main()
