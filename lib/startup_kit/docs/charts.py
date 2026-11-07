"""Chart images for documents (DOCX/PDF), styled with the active theme.

Rules enforced here (shared with the deck engine): a chart needs data and a
source or evidence reference; no 3D, no gridline clutter, values labelled.
"""
from __future__ import annotations

import os
from typing import Dict, List, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from ..render.base import format_value  # noqa: E402


def validate_chart(data: Dict) -> List[str]:
    errs = []
    if data.get("_error"):
        errs.append(f"chart YAML invalid: {data['_error']}")
        return errs
    cats = data.get("categories") or []
    series = data.get("series") or ([{"name": data.get("name", ""), "values": data.get("values")}]
                                    if data.get("values") is not None else [])
    if not cats or not series:
        errs.append("chart needs categories and values/series")
    for s in series:
        if len(s.get("values") or []) != len(cats):
            errs.append(f"series '{s.get('name', '')}' has {len(s.get('values') or [])} values for {len(cats)} categories")
    if not (data.get("source") or data.get("evidence")):
        errs.append("chart needs a source or evidence reference")
    return errs


def render_chart(data: Dict, theme, path: str, width_in=6.3, height_in=3.0, dpi=220) -> str:
    cats = [str(c) for c in data.get("categories", [])]
    series = data.get("series") or [{"name": data.get("name", ""), "values": data.get("values")}]
    kind = data.get("kind", "column")
    fmt, prefix, suffix = data.get("format", "number"), data.get("prefix", ""), data.get("suffix", "")
    colors = theme.palette(max(len(series), 1))
    hl = data.get("highlight")
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": [theme.body_font, "Arial", "Helvetica", "DejaVu Sans"],
                         "font.size": 8.5, "axes.edgecolor": theme.rule, "axes.labelcolor": theme.muted,
                         "xtick.color": theme.muted, "ytick.color": theme.muted})
    fig, ax = plt.subplots(figsize=(width_in, height_in), dpi=dpi)
    fig.patch.set_facecolor("white")
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", length=0)
    n = len(series)
    xs = list(range(len(cats)))
    if kind == "line":
        for i, s in enumerate(series):
            ax.plot(xs, s["values"], color=colors[i], lw=2, marker="o", ms=4, label=s.get("name"))
            for x, v in zip(xs, s["values"]):
                if v is not None and (len(xs) <= 8 or x == xs[-1]):
                    ax.annotate(format_value(v, fmt, prefix, suffix), (x, v), textcoords="offset points", xytext=(0, 6),
                                ha="center", fontsize=7.5, color=theme.ink, fontweight="bold")
        ax.set_xticks(xs)
        ax.set_xticklabels(cats)
        ax.set_yticks([])
    elif kind == "bar":
        vals = series[0]["values"]
        ys = list(range(len(cats)))[::-1]
        cols = [colors[0] if hl in (None, i) else theme.rule for i in range(len(cats))]
        ax.barh(ys, vals, color=cols, height=0.6)
        ax.set_yticks(ys)
        ax.set_yticklabels(cats)
        ax.set_xticks([])
        ax.spines["bottom"].set_visible(False)
        ax.spines["left"].set_visible(True)
        for y, v in zip(ys, vals):
            ax.text(v, y, "  " + format_value(v, fmt, prefix, suffix), va="center", fontsize=7.5, color=theme.ink,
                    fontweight="bold")
    else:
        width = 0.7 / (1 if kind == "stacked-column" else n)
        bottoms = [0.0] * len(cats)
        for i, s in enumerate(series):
            vals = [v or 0 for v in s["values"]]
            if kind == "stacked-column":
                pos = xs
                bars = ax.bar(pos, vals, width, bottom=bottoms, color=colors[i], label=s.get("name"))
                bottoms = [b + v for b, v in zip(bottoms, vals)]
            else:
                pos = [x - 0.35 + width * (i + 0.5) for x in xs]
                cols = colors[i] if not (n == 1 and hl is not None) else [colors[0] if j == hl else theme.rule
                                                                          for j in range(len(cats))]
                bars = ax.bar(pos, vals, width * 0.92, color=cols, label=s.get("name"))
                for b, v in zip(bars, vals):
                    ax.text(b.get_x() + b.get_width() / 2, b.get_height(), format_value(v, fmt, prefix, suffix),
                            ha="center", va="bottom", fontsize=7.5, color=theme.ink, fontweight="bold")
        if kind == "stacked-column":
            for x, tot in zip(xs, bottoms):
                ax.text(x, tot, format_value(tot, fmt, prefix, suffix), ha="center", va="bottom", fontsize=7.5,
                        color=theme.ink, fontweight="bold")
        ax.set_xticks(xs)
        ax.set_xticklabels(cats)
        ax.set_yticks([])
    if n > 1:
        ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(0, 1.12), ncol=min(n, 4), fontsize=7.5)
    fig.tight_layout()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig.savefig(path, dpi=dpi, facecolor="white")
    plt.close(fig)
    return path
