"""Design tokens and audience themes.

A theme is a small set of tokens (colors, type scale, spacing) shared by the
deck, document and spreadsheet renderers so every artifact for a startup looks
like it came from the same studio.  Brand overrides come from
``startup-profile/profile.yaml`` (``brand:`` block) or a theme YAML file.

Fonts: Office files reference font *names*, which must exist on the reader's
machine, so the defaults are universally available faces (Georgia, Arial).
PDFs embed TrueType files when found on the system and otherwise fall back to
the PDF core fonts with near-identical metrics (Times / Helvetica).
"""
from __future__ import annotations

import copy
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import yaml


def hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a: str, b: str, t: float) -> str:
    """Blend colour a toward b by t (0..1)."""
    ra, ga, ba = hex_to_rgb(a)
    rb, gb, bb = hex_to_rgb(b)
    return "#%02X%02X%02X" % (round(ra + (rb - ra) * t), round(ga + (gb - ga) * t), round(ba + (bb - ba) * t))


def luminance(h: str) -> float:
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = hex_to_rgb(h)
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a: str, b: str) -> float:
    la, lb = sorted([luminance(a), luminance(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


@dataclass
class Theme:
    name: str
    audience: str
    # colour tokens
    ink: str = "#14171A"          # primary text
    muted: str = "#5B6470"        # secondary text
    faint: str = "#9AA3AD"        # captions, footers
    rule: str = "#D9DDE1"         # hairlines
    paper: str = "#FFFFFF"        # page / slide background
    tint: str = "#F3F4F1"         # panels
    accent: str = "#1F5C4A"       # single brand accent
    accent_2: str = "#C8743A"     # secondary highlight, used sparingly
    positive: str = "#2E7D5B"
    warning: str = "#B7791F"
    negative: str = "#B4423A"
    # typography
    heading_font: str = "Georgia"
    body_font: str = "Arial"
    mono_font: str = "Courier New"
    # deck type scale (pt)
    deck_title: float = 30
    deck_display: float = 44
    deck_body: float = 15
    deck_small: float = 11
    deck_caption: float = 9
    # document type scale (pt)
    doc_body: float = 10.5
    doc_h1: float = 20
    doc_h2: float = 14
    doc_h3: float = 11.5
    doc_small: float = 8.5
    # layout
    cover_style: str = "editorial"   # editorial | institutional | minimal
    numbered_headings: bool = False
    chart_palette: List[str] = field(default_factory=list)
    logo: Optional[str] = None

    def palette(self, n: int) -> List[str]:
        """Chart colours: accent first, then tonal steps, never rainbow."""
        if self.chart_palette:
            base = list(self.chart_palette)
        else:
            base = [self.accent, mix(self.accent, self.paper, 0.45), self.accent_2,
                    mix(self.accent, self.ink, 0.45), mix(self.accent_2, self.paper, 0.45),
                    self.muted, mix(self.muted, self.paper, 0.5)]
        while len(base) < n:
            base = base + [mix(c, self.paper, 0.3) for c in base]
        return base[:n]

    @property
    def status_colors(self) -> Dict[str, str]:
        return {
            "live": self.positive,
            "built": mix(self.positive, self.paper, 0.35),
            "in-development": self.warning,
            "planned": self.muted,
            "proposed": self.faint,
            "unknown": self.negative,
        }

    def check(self) -> List[str]:
        """Accessibility warnings (WCAG contrast)."""
        warnings = []
        for label, fg in (("ink", self.ink), ("muted", self.muted), ("accent", self.accent)):
            c = contrast(fg, self.paper)
            if c < 4.5:
                warnings.append(f"{label} {fg} on paper {self.paper} has contrast {c:.2f} < 4.5")
        return warnings


STATUS_LABELS = {
    "live": "Live",
    "built": "Built, not launched",
    "in-development": "In development",
    "planned": "Planned",
    "proposed": "Proposed",
    "unknown": "Unverified",
}

_BASE = {
    # Venture capital: confident, editorial, lots of white space.
    "venture": dict(audience="venture-capital"),
    # Angel: same system, warmer accent.
    "angel": dict(audience="angel", accent="#7A3E2B", accent_2="#2D5D7B"),
    # Accelerator applications: crisp, minimal.
    "accelerator": dict(audience="accelerator", heading_font="Arial", accent="#C2410C", accent_2="#1F2937",
                        cover_style="minimal"),
    # Corporate partners: restrained navy, sans throughout.
    "corporate": dict(audience="corporate-partner", heading_font="Arial", accent="#1E3A5F", accent_2="#8A6D3B",
                      cover_style="institutional"),
    # Government / grant: conservative, numbered sections, high legibility.
    "institutional": dict(audience="government", heading_font="Arial", accent="#123B6D", accent_2="#5A6E2F",
                          cover_style="institutional", numbered_headings=True, doc_body=11),
    # Internal team documents.
    "internal": dict(audience="internal", heading_font="Arial", accent="#334155", accent_2="#0F766E",
                     cover_style="minimal"),
}

AUDIENCE_TO_THEME = {
    "vc": "venture", "venture-capital": "venture", "investor": "venture", "seed": "venture",
    "angel": "angel", "accelerator": "accelerator", "corporate": "corporate", "partner": "corporate",
    "corporate-partner": "corporate", "government": "institutional", "grant": "institutional",
    "internal": "internal", "team": "internal",
}


def available_themes() -> List[str]:
    return sorted(_BASE)


def get_theme(name_or_audience: str = "venture", brand: Optional[dict] = None) -> Theme:
    key = AUDIENCE_TO_THEME.get(name_or_audience, name_or_audience)
    if key not in _BASE:
        raise ValueError(f"Unknown theme '{name_or_audience}'. Available: {', '.join(available_themes())}")
    theme = Theme(name=key, **copy.deepcopy(_BASE[key]))
    if brand:
        apply_brand(theme, brand)
    return theme


_BRAND_KEYS = {"accent", "accent_2", "ink", "muted", "paper", "tint", "heading_font", "body_font",
               "chart_palette", "logo", "positive", "warning", "negative"}


def apply_brand(theme: Theme, brand: dict) -> Theme:
    """Apply startup brand tokens.  Unknown keys are ignored deliberately."""
    for k, v in (brand or {}).items():
        k2 = k.replace("-", "_")
        if k2 in _BRAND_KEYS and v:
            setattr(theme, k2, v)
    return theme


def load_theme_file(path: str, base: str = "venture") -> Theme:
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    theme = get_theme(data.get("base", base))
    apply_brand(theme, data)
    if data.get("logo") and not os.path.isabs(data["logo"]):
        theme.logo = os.path.join(os.path.dirname(os.path.abspath(path)), data["logo"])
    return theme
