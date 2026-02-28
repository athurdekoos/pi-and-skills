"""
Brand token loader and theme builder.
Reads brand.json and produces runtime config objects.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from pptx.dml.color import RGBColor


# ---------------------------------------------------------------------------
# Brand Config (loaded from brand.json)
# ---------------------------------------------------------------------------

@dataclass
class BrandConfig:
    """All brand tokens loaded from brand.json."""
    colors: Dict[str, str] = field(default_factory=dict)
    color_roles: Dict[str, str] = field(default_factory=dict)
    gradient: Dict[str, Any] = field(default_factory=dict)
    typography: Dict[str, str] = field(default_factory=dict)
    type_scale_pt: Dict[str, int] = field(default_factory=dict)
    spacing_inches: Dict[str, float] = field(default_factory=dict)
    card_style: Dict[str, Any] = field(default_factory=dict)
    button_style: Dict[str, Any] = field(default_factory=dict)
    logo_rules: Dict[str, Any] = field(default_factory=dict)
    logo_assets: Dict[str, str] = field(default_factory=dict)
    website_cues: Dict[str, Any] = field(default_factory=dict)
    slide_dimensions: Dict[str, Any] = field(default_factory=dict)

    def color(self, name: str) -> str:
        """Get hex color by name."""
        return self.colors.get(name, "#000000")

    def role_color(self, role: str) -> str:
        """Get hex color by role name (resolves through color_roles)."""
        color_name = self.color_roles.get(role, "black")
        return self.color(color_name)

    def rgb(self, name: str) -> RGBColor:
        hex_val = self.color(name).lstrip("#")
        return RGBColor(int(hex_val[:2], 16), int(hex_val[2:4], 16), int(hex_val[4:6], 16))


def load_brand(brand_json_path: str, skill_dir: str = None) -> BrandConfig:
    """Load brand.json and resolve logo asset paths to absolute paths.

    Args:
        brand_json_path: Path to brand.json
        skill_dir: The skill root directory (for resolving relative logo paths).
                   If None, uses the parent of the brand.json file's directory.
    """
    with open(brand_json_path) as f:
        data = json.load(f)

    if skill_dir is None:
        # brand.json is at <skill_dir>/references/brand.json
        skill_dir = str(Path(brand_json_path).resolve().parent.parent)

    brand = BrandConfig(
        colors=data.get("colors", {}),
        color_roles=data.get("color_roles", {}),
        gradient=data.get("gradient", {}),
        typography=data.get("typography", {}),
        type_scale_pt=data.get("type_scale_pt", {}),
        spacing_inches=data.get("spacing_inches", {}),
        card_style=data.get("card_style", {}),
        button_style=data.get("button_style", {}),
        logo_rules=data.get("logo_rules", {}),
        logo_assets={},
        website_cues=data.get("website_cues", {}),
        slide_dimensions=data.get("slide_dimensions", {}),
    )

    # Resolve logo asset paths to absolute
    for key, rel_path in data.get("logo_assets", {}).items():
        abs_path = os.path.join(skill_dir, rel_path)
        brand.logo_assets[key] = abs_path

    return brand


# ---------------------------------------------------------------------------
# Theme Config (runtime config for slide building)
# ---------------------------------------------------------------------------

@dataclass
class ThemeConfig:
    """Merged theme: brand tokens + derived layout values."""
    brand: BrandConfig = field(default_factory=BrandConfig)

    # Shortcut color accessors (populated from brand)
    night_navy: str = "#022791"
    day_blue: str = "#4D75FE"
    salmon: str = "#FF8A69"
    yellow: str = "#FAA944"
    black: str = "#0C0C0C"
    gray: str = "#262626"
    white: str = "#FFFFFF"

    # Typography
    headline_font: str = "Inter Tight"
    body_font: str = "Inter Tight"
    utility_font: str = "Roboto"
    fallback_font: str = "Arial"

    # Type scale
    h1_size: int = 44
    h2_size: int = 32
    h3_size: int = 24
    h4_size: int = 18
    body_size: int = 14
    body_lg_size: int = 18
    small_size: int = 11
    caption_size: int = 10

    # Spacing
    margin_inches: float = 0.6
    gutter_inches: float = 0.35
    section_pad_inches: float = 0.5

    # Card styles
    card_radius_pt: int = 12
    card_shadow_alpha: int = 15

    # Button styles
    button_radius_pt: int = 20
    button_fill_color: str = "#4D75FE"
    button_text_color: str = "#FFFFFF"

    # Slide dimensions
    slide_width_inches: float = 13.333
    slide_height_inches: float = 7.5

    # Logo paths (absolute)
    logo_colored_horizontal: str = ""
    logo_colored_vertical: str = ""
    logo_white_horizontal: str = ""
    logo_black_horizontal: str = ""
    favicon_colored: str = ""
    favicon_white: str = ""


def build_theme(brand: BrandConfig) -> ThemeConfig:
    """Build a ThemeConfig from a BrandConfig."""
    theme = ThemeConfig(brand=brand)

    # Colors
    theme.night_navy = brand.color("night_navy")
    theme.day_blue = brand.color("day_blue")
    theme.salmon = brand.color("salmon")
    theme.yellow = brand.color("yellow")
    theme.black = brand.color("black")
    theme.gray = brand.color("gray")
    theme.white = brand.color("white")

    # Typography
    typo = brand.typography
    theme.headline_font = typo.get("headline_font", "Inter Tight")
    theme.body_font = typo.get("body_font", "Inter Tight")
    theme.utility_font = typo.get("utility_font", "Roboto")
    theme.fallback_font = typo.get("fallback", "Arial")

    # Type scale
    ts = brand.type_scale_pt
    theme.h1_size = ts.get("h1", 44)
    theme.h2_size = ts.get("h2", 32)
    theme.h3_size = ts.get("h3", 24)
    theme.h4_size = ts.get("h4", 18)
    theme.body_size = ts.get("body", 14)
    theme.body_lg_size = ts.get("body_lg", 18)
    theme.small_size = ts.get("small", 11)
    theme.caption_size = ts.get("caption", 10)

    # Spacing
    sp = brand.spacing_inches
    theme.margin_inches = sp.get("margin", 0.6)
    theme.gutter_inches = sp.get("gutter", 0.35)
    theme.section_pad_inches = sp.get("section_pad", 0.5)

    # Card style
    cs = brand.card_style
    theme.card_radius_pt = cs.get("radius_pt", 12)
    theme.card_shadow_alpha = cs.get("shadow_alpha_pct", 15)

    # Button style
    bs = brand.button_style
    theme.button_radius_pt = bs.get("radius_pt", 20)
    # Resolve fill_color from brand color name or hex
    fill = bs.get("fill_color", "day_blue")
    theme.button_fill_color = brand.color(fill) if not fill.startswith("#") else fill
    text_c = bs.get("text_color", "white")
    theme.button_text_color = brand.color(text_c) if not text_c.startswith("#") else text_c

    # Slide dimensions
    sd = brand.slide_dimensions
    theme.slide_width_inches = sd.get("width_inches", 13.333)
    theme.slide_height_inches = sd.get("height_inches", 7.5)

    # Logo paths
    la = brand.logo_assets
    theme.logo_colored_horizontal = la.get("colored_horizontal_png", "")
    theme.logo_colored_vertical = la.get("colored_vertical_png", "")
    theme.logo_white_horizontal = la.get("white_horizontal_png", "")
    theme.logo_black_horizontal = la.get("black_horizontal_png", "")
    theme.favicon_colored = la.get("favicon_colored_png", "")
    theme.favicon_white = la.get("favicon_white_png", "")

    return theme
