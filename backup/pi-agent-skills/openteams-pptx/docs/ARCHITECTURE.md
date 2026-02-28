# Architecture

How the OpenTeams PPTX generator is structured, why decisions were made, and how data flows from brand config to rendered slides.

## Design Goals

1. **Brand compliance by default** — impossible to generate off-brand slides
2. **Separation of concerns** — brand tokens, layout logic, and rendering are independent
3. **Easy to extend** — adding a new slide type is one function + one registry entry
4. **CLI + agent friendly** — works from command line or as a pi agent skill

## Module Overview

```
┌─────────────────────────────────────────────────────┐
│                   generate_deck.py                  │
│              CLI entry point + validation            │
│                                                     │
│  ┌──────────────┐  ┌────────────┐  ┌─────────────┐ │
│  │ brand_engine  │→│slide_builder│→│slide_renderers│ │
│  │ (config)      │  │ (helpers)  │  │ (per-type)   │ │
│  └──────┬───────┘  └─────┬──────┘  └──────┬──────┘ │
│         │                │                 │        │
│         │          ┌─────┴──────┐          │        │
│         │          │pptx_helpers│          │        │
│         │          │ (low-level)│          │        │
│         │          └────────────┘          │        │
│         ▼                                  ▼        │
│    brand.json                         .pptx file    │
└─────────────────────────────────────────────────────┘
```

### `brand_engine.py` — Configuration Layer

**Purpose:** Load `brand.json` and produce typed runtime config objects.

- `BrandConfig` — dataclass holding raw brand tokens (colors, typography, spacing, logo rules, logo paths)
- `ThemeConfig` — dataclass with resolved, ready-to-use values (hex colors, font names, absolute logo paths, card/button styles)
- `load_brand()` — reads JSON, resolves relative logo paths to absolute
- `build_theme()` — transforms `BrandConfig` → `ThemeConfig`

**Key decision:** Logo paths in `brand.json` are relative to the skill directory. `load_brand()` resolves them at load time so renderers never deal with path logic.

### `slide_builder.py` — High-Level Helpers

**Purpose:** Branded shape-building API that renderers use.

`SlideBuilder` wraps a `python-pptx` `Presentation` and a `ThemeConfig` to provide:

| Method | What It Does |
|--------|-------------|
| `new_slide()` | Add blank slide |
| `add_title()` | Headline text box (Inter Tight Bold, Night Navy) |
| `add_subtitle()` | Subtitle text box (Inter Tight, Day Blue) |
| `add_body()` | Body text with line splitting and spacing |
| `add_bullet_list()` | Bulleted list with branded bullet dots |
| `add_logo()` | Place logo with correct variant, position, and sizing |
| `add_accent_bar()` | Thin colored bar (used under titles) |
| `add_card()` | Rounded rectangle with shadow and radius |
| `add_button()` | Pill-shaped button with centered text |
| `add_placeholder_image()` | Light blue rounded rect with label |
| `add_footer()` | Copyright text + favicon |
| `add_section_header()` | Full dark-background section divider |
| `add_metric_card()` | KPI card with value, label, accent bar |

Also provides `ACCENT_ROTATION` — the standard cycling color list used by agenda, metrics, team, and case study slides.

**Key decision:** All styling flows through `ThemeConfig` — renderers never hardcode colors or fonts.

### `slide_renderers.py` — Per-Type Render Functions

**Purpose:** One function per slide type, each producing one slide.

Each renderer has the signature:
```python
def render_<type>(sb: SlideBuilder, spec: dict) -> None
```

The `RENDERERS` dict maps type strings to functions:
```python
RENDERERS = {
    "cover":            render_cover,
    "section_divider":  render_section_divider,
    ...
}
```

**Key decision:** Renderers are pure functions that receive a `SlideBuilder` and a spec dict. No global state, no side effects beyond adding shapes to the slide.

### `pptx_helpers.py` — Low-Level Utilities

**Purpose:** XML-level operations that `python-pptx` doesn't support natively.

- `hex_to_rgbcolor()` — safe hex → RGBColor conversion with fallback
- `luminance()` / `contrast_ratio()` / `auto_text_color()` — WCAG-based color accessibility
- `set_shape_fill()` / `set_no_border()` — shape styling
- `make_gradient_rect()` — gradient fill via direct XML manipulation
- `set_shape_alpha()` — transparency on solid or gradient fills
- `set_shape_rounded_rect_radius()` — corner radius via XML

**Key decision:** These helpers edit `lxml` elements directly because `python-pptx` has no API for gradients, transparency, or custom corner radii.

### `generate_deck.py` — CLI Entry Point

**Purpose:** Parse arguments, validate spec, orchestrate generation.

Flow:
1. Parse CLI args (`--spec`, `--demo`, `--brand`, `--out`) or read stdin
2. `validate_spec()` — check all slides have valid types and required fields
3. `load_brand()` → `build_theme()` — build runtime config
4. Create `Presentation` + `SlideBuilder`
5. Loop through slides, dispatch to `RENDERERS[type]`
6. Save `.pptx`

Also contains `DEMO_SPEC` — a 10-slide spec exercising all slide types, used for `--demo` mode.

### `refresh_site_style.py` — Website Crawler

**Purpose:** Update `website_cues` in `brand.json` by crawling openteams.com.

Extracts CSS variables, border-radius values, box-shadow patterns, and background colors. Merges into `brand.json` without touching immutable brand tokens.

**Safety:** Only follows same-origin URLs (SSRF protection via `_is_same_origin()`). Caps at 4 pages and 200KB of CSS per external stylesheet.

## Data Flow

```
User prompt
    ↓
Claude builds JSON slide spec
    ↓
generate_deck.py validates spec
    ↓
brand.json → load_brand() → BrandConfig → build_theme() → ThemeConfig
    ↓
SlideBuilder(Presentation, ThemeConfig)
    ↓
For each slide in spec:
    RENDERERS[type](slide_builder, slide_spec)
        → slide_builder.add_title() / add_card() / add_logo() / ...
            → pptx_helpers (XML manipulation)
    ↓
Presentation.save("output.pptx")
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **JSON spec as intermediate format** | Decouples content (what to say) from rendering (how it looks). Claude generates JSON; Python renders it. |
| **Blank slide layout only** | We build every element from scratch rather than using PowerPoint templates. Full control, no template conflicts. |
| **Brand tokens in JSON, not code** | Colors/fonts/spacing can be updated without touching Python. Non-developers can review brand.json. |
| **SlideBuilder as facade** | Renderers stay simple — they call `sb.add_card()` not raw `python-pptx` + XML. |
| **WCAG contrast checking** | `auto_text_color()` ensures text is always readable regardless of background color. |
| **Accent color rotation** | Consistent visual rhythm across slides — the same 4-color cycle everywhere. |
| **Max 6 team members** | Layout constraint — more than 6 cards don't fit on a 16:9 slide. Logged warning when truncating. |
