# OpenTeams PPTX Generator

A [pi](https://github.com/mariozechner/pi-coding-agent) agent skill that generates professional, brand-compliant OpenTeams PowerPoint presentations from natural language.

## What It Does

Ask Claude to make a presentation and it handles everything — content structure, slide layout, brand compliance, and `.pptx` generation. You get a polished deck in seconds.

**Supports 11 slide types:** cover, section divider, agenda, content, two-column, quote, metrics, team, case study, closing, and blank.

## Using the Skill with Claude

### How It Works

When you ask Claude to create a presentation, the skill activates automatically. Here's the typical flow:

**1. You describe what you need:**
> "Create a 10-slide pitch deck for IBM about our open source platform"

**2. Claude asks clarifying questions** (if needed):
- Purpose — pitch deck, internal update, client proposal?
- Audience — clients, partners, investors?
- Slide count — typically 8–15
- Key messages — what should each slide communicate

**3. Claude builds the deck:**
- Selects appropriate slide types for your content
- Writes a JSON slide spec
- Runs the generator
- Presents the output file path

**4. You review and iterate:**
> "Make the metrics slide show 4 KPIs instead of 3"
> "Change the closing slide CTA to 'Schedule a Demo'"

Claude regenerates and you get an updated file.

### Example Prompts

| Prompt | What You Get |
|--------|-------------|
| "Create a pitch deck for Acme Corp" | 10-slide client proposal with cover, agenda, content slides, metrics, and closing |
| "Make me an internal update with 5 slides" | Compact deck with cover, content slides, and closing |
| "Build a case study presentation for the Global Bank project" | Deck featuring challenge → solution → results layout |
| "Generate a demo deck showing all slide types" | All 11 slide types with placeholder content |

### Example Conversation

Here's what a full interaction looks like from start to finish:

---

**You:**
> Create a presentation for a meeting with Capital One about adopting our open source management platform.

**Claude:**
> Got it — a client pitch deck for Capital One. A few quick questions so I can tailor the deck:
>
> 1. **How many slides** are you thinking? A focused 8–10 or a more comprehensive 12–15?
> 2. **What's the main goal** of this meeting — introductory awareness, a technical deep-dive, or closing a deal?
> 3. **Any specific numbers or wins** you'd like to highlight? (e.g., cost savings, adoption stats, case studies)
> 4. **Should I include a team slide** introducing who they'll be working with?

**You:**
> 10 slides, it's an intro meeting. Highlight our 500+ open source projects managed, 40% cost reduction for clients, and the Global Bank case study. No team slide needed.

**Claude:**
> Perfect. Here's the deck structure I'll build:
>
> | # | Slide Type | Content |
> |---|-----------|---------|
> | 1 | `cover` | "Open Source at Scale — A Platform for Capital One" |
> | 2 | `agenda` | Meeting topics overview |
> | 3 | `content` | The open source management challenge |
> | 4 | `content` | OpenTeams platform overview |
> | 5 | `two_column` | Before vs. After: unmanaged vs. managed open source |
> | 6 | `metrics` | 500+ projects, 40% cost reduction, 99.9% uptime |
> | 7 | `case_study` | Global Bank — Challenge → Solution → Results |
> | 8 | `quote` | Client testimonial |
> | 9 | `content` | Implementation roadmap & next steps |
> | 10 | `closing` | CTA: "Schedule a Technical Deep-Dive" |
>
> Does this look right, or would you like to adjust any slides?

**You:**
> Looks great, go ahead.

**Claude:**
> ✅ Generated: `capital_one_pitch.pptx` (10 slides, 16:9 widescreen)
>
> The deck uses Night Navy/Day Blue branding, Inter Tight typography, and the colored OpenTeams logo on light slides with the white logo on the dark quote and closing slides. Ready to open in PowerPoint or upload to Google Slides.

**You:**
> Can you change the metrics slide to show 4 KPIs instead of 3? Add "200+ enterprise clients".

**Claude:**
> ✅ Updated: `capital_one_pitch.pptx` — metrics slide now shows 4 KPI cards:
> - 500+ open source projects
> - 40% cost reduction
> - 99.9% uptime
> - 200+ enterprise clients

---

### Expected Output

The skill generates a `.pptx` file in the current working directory. Each deck includes:

- **Widescreen (16:9)** format at 13.333" × 7.5"
- **OpenTeams branding** — Night Navy/Day Blue palette, Inter Tight font, proper logo placement
- **Professional layouts** — cards with shadows, accent bars, gradient backgrounds, pill buttons
- **Footer on every slide** — copyright text and favicon

The file opens in PowerPoint, Google Slides, LibreOffice Impress, or Keynote.

### Uploading to Google Slides

To use your generated deck in Google Slides:

1. Go to [Google Drive](https://drive.google.com)
2. Click **New** → **File upload** and select the `.pptx` file
3. Once uploaded, double-click the file — Drive will show a preview
4. Click **Open with Google Slides** at the top
5. Google Slides converts the file automatically, preserving layouts, colors, and text

> **Tip:** To save it permanently as a Google Slides file, go to **File** → **Save as Google Slides** after opening. This lets you collaborate and edit natively without the `.pptx` wrapper.

> **Note:** Custom fonts (Inter Tight) may fall back to Arial in Google Slides if they aren't available in your Google Workspace. To fix this, open the deck, select all text (**Ctrl+A**), and apply Inter Tight from the font menu — Google Slides includes it in its font library.

### Trigger Phrases

The skill activates when you mention:
- "presentation", "slide deck", "pitch deck", "powerpoint", "pptx"
- "slides", "deck", "presentation template"
- Creating content for clients, partners, or stakeholders

## Installation

### For pi (coding agent)

```bash
./install_pi_plugin.sh
```

The skill becomes available as `/skill:openteams-pptx` in any pi session.

### For Claude Code

```bash
./install_claude_plugin.sh
```

The skill is installed to `~/.agents/skills/openteams-pptx/`.

### Prerequisites

- **Python 3.11+** with `python-pptx` installed:
  ```bash
  pip3 install python-pptx
  ```
- The installers check for prerequisites and warn if anything is missing.

## Quick Start (Manual CLI)

### Generate a Deck

**From a slide spec JSON:**
```bash
python3 scripts/generate_deck.py \
  --spec slides.json \
  --brand references/brand.json \
  --out output.pptx
```

**Demo deck (all slide types with placeholder content):**
```bash
python3 scripts/generate_deck.py \
  --demo \
  --brand references/brand.json \
  --out demo.pptx
```

**Pipe JSON from stdin:**
```bash
echo '{"slides":[{"type":"cover","title":"Hello"}]}' | \
  python3 scripts/generate_deck.py \
  --brand references/brand.json \
  --out quick.pptx
```

### Slide Spec Format

```json
{
  "title": "Deck Title",
  "slides": [
    {"type": "cover", "title": "Main Title", "subtitle": "Tagline", "date": "February 2026"},
    {"type": "agenda", "items": ["Topic 1", "Topic 2", "Topic 3"]},
    {"type": "content", "title": "Key Point", "body": "Details here."},
    {"type": "closing", "title": "Thank You", "contact": "hello@openteams.com"}
  ]
}
```

See [`references/slide_types.md`](references/slide_types.md) for the full schema of all 11 slide types and their required/optional fields.

## Slide Types

| Type | Purpose | Key Fields |
|------|---------|------------|
| `cover` | Opening hero slide | `title`, `subtitle?`, `date?` |
| `section_divider` | Dark section separator | `title`, `subtitle?` |
| `agenda` | Numbered topic list | `items[]` |
| `content` | Title + body + image area | `title`, `body?`, `bullet_items?`, `image_placeholder?` |
| `two_column` | Side-by-side comparison | `title`, `left_title`, `left_body?`, `right_title`, `right_body?` |
| `quote` | Big statement, dark background | `text`, `attribution?` |
| `metrics` | KPI cards + chart area | `title`, `metrics[{value, label}]` |
| `team` | Profile cards (max 6) | `title`, `members[{name, role, bio?}]` |
| `case_study` | Challenge → Solution → Results | `title`, `challenge`, `solution`, `results` |
| `closing` | CTA with contact info | `title`, `subtitle?`, `contact?`, `cta_text?` |
| `blank` | Empty slide with logo | _(none)_ |

## Brand Compliance

These rules are enforced automatically and come from the [OpenTeams 2025 Brand Guidelines](../OpenTeams_Brand_Guidelines_2025.pdf):

| Element | Rule |
|---------|------|
| **Primary colors** | Night Navy `#022791`, Day Blue `#4D75FE` |
| **Accent colors** | Salmon `#FF8A69`, Yellow `#FAA944` — accents only, never dominant |
| **Headlines** | Inter Tight Bold |
| **Body text** | Inter Tight Regular |
| **Utility text** | Roboto (footers, captions) |
| **Logo placement** | Upper-left or lower-left/center — **never right-aligned** |
| **Logo on dark backgrounds** | White variant only |
| **Backgrounds** | White-dominant; dark (Night Navy) for dividers, quotes, closing only |
| **Gradients** | Night Navy → Day Blue for cover and closing slides only |
| **Cover slide** | No decorative dots on the gradient panel |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **`python3: command not found`** | Install Python 3: `sudo apt install python3` (Ubuntu/Debian) or `brew install python3` (macOS) |
| **`ModuleNotFoundError: No module named 'pptx'`** | Install python-pptx: `pip3 install python-pptx` |
| **Permission denied running installer** | Make it executable: `chmod +x install_pi_plugin.sh` |
| **Fonts look wrong (Arial instead of Inter Tight)** | Install Inter Tight font system-wide, or accept Arial fallback. In Google Slides, select all text and apply Inter Tight from the font menu. |
| **Logo not appearing on slides** | Verify `assets/logos/` contains 6 PNG files. Run `ls assets/logos/*.png` to check. |

## Running Tests

```bash
pip3 install pytest
python3 -m pytest tests/ -v
```

Tests cover color utilities, spec validation, and smoke-test generation for all slide types.

## Directory Structure

```
openteams-pptx/
├── SKILL.md                       # Pi agent skill definition
├── README.md                      # This file
├── assets/
│   └── logos/                     # Bundled logo PNGs (6 files)
├── references/
│   ├── brand.json                 # Brand tokens (colors, fonts, spacing, logos)
│   └── slide_types.md             # Slide type catalog and JSON schema
├── scripts/
│   ├── generate_deck.py           # CLI entry point + spec validation
│   ├── brand_engine.py            # Brand config loader + ThemeConfig builder
│   ├── slide_builder.py           # SlideBuilder class (high-level shape helpers)
│   ├── slide_renderers.py         # Per-slide-type render functions
│   ├── pptx_helpers.py            # Low-level shape/gradient/shadow helpers
│   └── refresh_site_style.py      # Website crawler to refresh visual cues
└── tests/
    ├── test_core.py               # Unit + integration tests
    └── test_ai_readiness.json     # Sample 8-slide e2e test spec
```

## Refreshing Website Styles

If the OpenTeams website has been updated, refresh the visual cues in `brand.json`:

```bash
python3 scripts/refresh_site_style.py \
  --url https://openteams.com/ \
  --brand-json references/brand.json
```

This re-crawls the site and updates `website_cues` in `brand.json` without touching immutable brand tokens (colors, typography, logo rules).
