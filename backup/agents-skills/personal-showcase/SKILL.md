---
name: personal-showcase
description: >
  Generate a stylish personal showcase / portfolio HTML page featuring projects, social links
  (GitHub, LinkedIn, Discord), and OpenTeams branding. Use this skill whenever the user asks
  to create a personal page, portfolio, link-in-bio, digital business card, project showcase,
  or landing page for themselves. Also trigger when the user mentions "my links", "my socials",
  "about me page", "personal site", "showcase my work", or wants to share their projects and
  contact info in a polished, visual format. Supports dark, light, and glassmorphism themes.
---

# Personal Showcase Generator

Generate a polished, animated HTML portfolio page that highlights projects and social links
with OpenTeams-inspired branding and smooth visual effects.

All paths below are relative to this skill's directory (the folder containing this SKILL.md).

## Overview

This skill produces a self-contained `.html` file — no server needed, no dependencies, just
open it in a browser. It features:

- **Animated hero section** with gradient avatar ring, name, handle, and tagline
- **Social link pills** for GitHub, LinkedIn, and Discord with branded hover effects
- **Project cards** with tags, highlights, and repo links
- **Three themes**: dark (Night Navy), light (clean white), glass (frosted blur)
- **Floating ambient orbs** in the OpenTeams accent palette (salmon, yellow, blue)
- **Fully responsive** — looks great on desktop and mobile

## How It Works

### Phase 1: Gather Info

Ask the user what they want on their page. Key info to collect:

- **Name and handle** — display name and username (e.g., `@athurdekoos`)
- **Tagline** — one-liner that describes what they do
- **Social links** — GitHub, LinkedIn, Discord URLs (any combo)
- **Projects** — name, description, repo URL, tags, highlight bullets
- **Theme preference** — dark (default), light, or glass

The default profile is pre-configured at `references/profile.json` with:

| Field | Default |
|-------|---------|
| Name | Amelia Thurdekoos |
| GitHub | [github.com/athurdekoos](https://github.com/athurdekoos) |
| LinkedIn | [linkedin.com/in/amelia-thurdekoos-26450b86](https://www.linkedin.com/in/amelia-thurdekoos-26450b86/) |
| Discord | [discord.gg/YmsT7FFnW8](https://discord.gg/YmsT7FFnW8) |
| Featured project | OpenTeams PPTX Generator |

If the user just says "generate my showcase" without details, use the defaults.

### Phase 2: Build or Update Profile

If the user provides custom info, create or update a `profile.json` following the schema
in `references/profile.json`. The structure is:

```json
{
  "name": "Display Name",
  "handle": "username",
  "tagline": "One-liner description",
  "socials": {
    "github": { "url": "https://github.com/...", "label": "GitHub", "icon": "github" },
    "linkedin": { "url": "https://linkedin.com/in/...", "label": "LinkedIn", "icon": "linkedin" },
    "discord": { "url": "https://discord.gg/...", "label": "Discord", "icon": "discord" }
  },
  "brand": {
    "night_navy": "#022791",
    "day_blue": "#4D75FE",
    "salmon": "#FF8A69",
    "yellow": "#FAA944",
    "accent_green": "#3AD58E"
  },
  "projects": [
    {
      "name": "Project Name",
      "description": "What it does",
      "repo": "https://github.com/...",
      "tags": ["python", "ai"],
      "highlights": ["Cool feature 1", "Cool feature 2"]
    }
  ]
}
```

Save the profile JSON to a temp file (e.g., `/tmp/showcase_profile.json`).

### Phase 3: Generate

Run the generator. Let `<skill-dir>` be the directory containing this SKILL.md:

```bash
python3 <skill-dir>/scripts/generate_showcase.py \
  --profile <profile-json-path> \
  --out <output-path>.html \
  --theme dark
```

**Theme options:**
- `dark` — Night Navy background, glowing accents (default)
- `light` — Clean white background, subtle shadows
- `glass` — Deep dark background with frosted glass card effects

Present the output file path to the user. They can open it directly in any browser.

### Phase 4: Iterate

The user might ask to:
- Change theme: regenerate with `--theme light` or `--theme glass`
- Add/remove projects or socials: update the profile JSON and regenerate
- Tweak the tagline or highlights: update and regenerate

## Adding More Socials

The generator supports GitHub, LinkedIn, and Discord out of the box. To add more social
platforms, add entries to the `socials` object in profile.json using one of the supported
icon keys. If the user needs a platform not yet supported, the icon SVGs live in
`scripts/generate_showcase.py` in the `ICONS` dict — new ones can be added there.

## Brand Alignment

The page uses OpenTeams brand colors and Inter Tight typography by default, keeping it
visually consistent with the OpenTeams PPTX Generator and other brand toolkit outputs.
The user can customize the `brand` object in profile.json to use different colors if they
want a personal brand instead.

## Tips

1. **Keep the tagline short** — one line, under 80 characters
2. **3–5 tags per project** works best visually
3. **2–4 highlight bullets** per project keeps cards scannable
4. **Dark theme** looks best for tech portfolios
5. **Glass theme** is the flashiest — great for sharing on social media
6. The HTML is fully self-contained — upload it anywhere (GitHub Pages, Netlify, etc.)
