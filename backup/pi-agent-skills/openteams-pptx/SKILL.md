---
name: openteams-pptx
description: >
  Generate modern, on-brand OpenTeams PowerPoint presentations from natural language.
  Use this skill whenever the user asks to create a presentation, slide deck, pitch deck,
  or .pptx file for OpenTeams. Also trigger when the user mentions "slides", "powerpoint",
  "deck", "presentation template", or wants to present OpenTeams content to clients,
  partners, or internal stakeholders. Covers cover slides, agendas, content layouts,
  metrics dashboards, team pages, case studies, quotes, and closing slides.
---

# OpenTeams PPTX Generator

Generate professional, brand-compliant OpenTeams PowerPoint presentations from natural-language prompts.

All paths below are relative to this skill's directory (the folder containing this SKILL.md).

## Overview

This skill produces `.pptx` files that follow the **OpenTeams 2025 Brand Guidelines** exactly.
It uses a bundled Python library with `python-pptx` to render slides from a JSON spec,
pulling colors, typography, spacing, logo assets, and visual cues from `references/brand.json`.

## How It Works

### Phase 1: Gather Content

Ask the user what the presentation is about. Determine:
- **Purpose** — pitch deck, internal update, client proposal, etc.
- **Audience** — clients, partners, internal stakeholders
- **Slide count** — typically 8–15 slides
- **Key messages** — what each slide should communicate

Read `references/slide_types.md` for the full catalog of available slide types and their required fields.

### Phase 2: Build Slide Spec

Create a JSON file following the schema in `references/slide_types.md`. Example:

```json
{
  "title": "Deck Title",
  "slides": [
    {"type": "cover", "title": "Main Title", "subtitle": "Tagline", "date": "February 2026"},
    {"type": "agenda", "items": ["Topic 1", "Topic 2", "Topic 3"]},
    {"type": "content", "title": "Key Point", "body": "Details here.", "image_placeholder": "Chart"},
    {"type": "closing", "title": "Thank You", "contact": "hello@openteams.com"}
  ]
}
```

Save the spec to a temporary JSON file (e.g., `/tmp/deck_spec.json`).

### Phase 3: Generate

Run the generation script. Let `<skill-dir>` be the directory containing this SKILL.md:

```bash
python3 <skill-dir>/scripts/generate_deck.py \
  --spec /tmp/deck_spec.json \
  --brand <skill-dir>/references/brand.json \
  --out <output-path>.pptx
```

The script validates the spec, renders each slide, and saves the `.pptx` file.
Present the output file path to the user.

## Brand Rules (Non-Negotiable)

These constraints come directly from the OpenTeams 2025 Brand Guidelines and must **never** be violated:

### Colors
- **Primary:** Night Navy `#022791` and Day Blue `#4D75FE`
- **Accents only:** Salmon `#FF8A69` and Yellow `#FAA944` — never as primary/dominant colors
- **Backgrounds:** White-dominant for most slides. Dark (Night Navy) only for section dividers, quotes, and closing
- **Gradients:** Night Navy → Day Blue for hero/cover and closing slides only

### Typography
- **Headlines:** Inter Tight Bold — always
- **Body text:** Inter Tight Regular — always
- **Utility text:** Roboto (footers, captions)
- **Never** use other fonts. Fallback to Arial only if Inter Tight is unavailable.

### Logo Usage
- **Placement:** Upper-left or lower-left/center only. **Never right-aligned.**
- **Colored logo** on white/light backgrounds
- **White logo** on dark/gradient backgrounds
- **Never** alter logo colors, add tagline text, distort, or add effects
- Minimum clearspace: width of the "O" in OpenTeams

## Website Visual Cues (Style Preference)

Softer guidelines derived from openteams.com — follow these for visual consistency:

- **Buttons:** Pill-shaped (fully rounded), Day Blue fill, white text
- **Cards:** Shadow-based elevation, no visible borders, 12pt corner radius
- **Whitespace:** Generous — 0.6" margins, 0.35" gutters
- **Decorative elements:** Translucent accent dots (circles) in yellow/salmon/blue at ~15–30% opacity — **never on the cover slide gradient panel** (they look like gray blobs next to the favicon)
- **Image placeholders:** Rounded corners, light blue (#E8EDFB) fill
- **Overall aesthetic:** Clean, minimal, white-dominant — avoid clutter

## Slide Types Reference

See `references/slide_types.md` for the complete catalog of all 11 slide types:

| Type | Purpose |
|------|---------|
| `cover` | Opening slide with hero layout |
| `section_divider` | Dark full-bleed section separator |
| `agenda` | Numbered topic list |
| `content` | Title + body + image placeholder |
| `two_column` | Side-by-side comparison |
| `quote` | Big statement on dark background |
| `metrics` | KPI cards with chart placeholder |
| `team` | Profile cards for team members |
| `case_study` | Challenge → Solution → Results |
| `closing` | CTA with contact info |
| `blank` | Empty slide with logo |

## Script Usage

**Generate from spec:**
```bash
python3 <skill-dir>/scripts/generate_deck.py \
  --spec <spec-file>.json \
  --brand <skill-dir>/references/brand.json \
  --out <output-path>.pptx
```

**Generate demo (all slide types with placeholder content):**
```bash
python3 <skill-dir>/scripts/generate_deck.py \
  --demo \
  --brand <skill-dir>/references/brand.json \
  --out <output-path>.pptx
```

**Pipe JSON from stdin:**
```bash
echo '{"slides":[...]}' | python3 <skill-dir>/scripts/generate_deck.py \
  --brand <skill-dir>/references/brand.json \
  --out <output-path>.pptx
```

Where `<skill-dir>` = the directory containing this SKILL.md (the absolute path to this skill's directory).

## Refreshing Website Styles

If the user mentions the OpenTeams website was recently updated, refresh the visual cues:

```bash
python3 <skill-dir>/scripts/refresh_site_style.py \
  --url https://openteams.com/ \
  --brand-json <skill-dir>/references/brand.json
```

This re-crawls the site and updates `website_cues` in `brand.json` without touching immutable brand tokens.

## Tips for Great Decks

1. **Keep slide count to 8–15** for most presentations
2. **One key message per slide** — don't overcrowd
3. **Always start with `cover`**, end with `closing`
4. **Use `agenda`** for decks with 5+ content slides
5. **Use `metrics`** for quantitative claims — numbers are persuasive
6. **Use `quote`** to break up dense sections and add emphasis
7. **Use `section_divider`** between major topics in longer decks
8. **Use `case_study`** for customer stories — the 3-column layout is compelling
9. **Match slide types to content** — don't force text into the wrong layout
10. **Review the output** — offer to regenerate if the user wants changes
