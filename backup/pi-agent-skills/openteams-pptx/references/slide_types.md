# Slide Type Catalog

This document describes every available slide type for the OpenTeams PPTX generator.
Use it to translate user requests into structured JSON slide specs.

---

## Deck Spec Schema

A full deck spec is a JSON object:

```json
{
  "title": "Deck title (used for filename)",
  "slides": [
    { "type": "cover", "title": "...", ... },
    { "type": "agenda", "items": [...] },
    ...
  ]
}
```

Each slide object must have a `"type"` field matching one of the IDs below,
plus the required fields for that type.

---

## Slide Types

### `cover`
**Purpose:** Opening slide — hero layout with gradient accent, logo, title, subtitle, CTA.
**Visual:** White left half with title text, Night Navy→Day Blue gradient on right with decorative dots and favicon.

| Field       | Required | Type   | Description                          |
|-------------|----------|--------|--------------------------------------|
| title       | ✅       | string | Main presentation title              |
| subtitle    | ❌       | string | Tagline or subtitle text             |
| date        | ❌       | string | Date string (e.g., "February 2026") |

---

### `section_divider`
**Purpose:** Full-bleed dark slide to separate major sections.
**Visual:** Night Navy background, accent bar, large title, optional subtitle. White logo at bottom-left.

| Field       | Required | Type   | Description                          |
|-------------|----------|--------|--------------------------------------|
| title       | ✅       | string | Section title                        |
| subtitle    | ❌       | string | Brief section description            |
| bg_color    | ❌       | string | Override background color (hex)      |

---

### `agenda`
**Purpose:** Numbered list of topics/sections for the presentation.
**Visual:** White background, numbered circles in rotating brand accent colors, item text beside each.

| Field       | Required | Type       | Description                     |
|-------------|----------|------------|---------------------------------|
| items       | ✅       | string[]   | List of agenda topic strings    |

---

### `content`
**Purpose:** General-purpose slide with title, body text, and optional image placeholder.
**Visual:** White background, accent bar, title top-left, body text left, image placeholder right.

| Field              | Required | Type   | Description                          |
|--------------------|----------|--------|--------------------------------------|
| title              | ✅       | string | Slide title                          |
| body               | ❌       | string | Body text (supports \n for newlines) |
| bullet_items       | ❌       | string[] | Bulleted list (alternative to body)|
| image_placeholder  | ❌       | string | Description for image placeholder    |

> Use either `body` or `bullet_items`, not both.

---

### `two_column`
**Purpose:** Side-by-side comparison or parallel content.
**Visual:** White background, two card-style columns with titles and body text.

| Field       | Required | Type   | Description                          |
|-------------|----------|--------|--------------------------------------|
| title       | ✅       | string | Slide title                          |
| left_title  | ✅       | string | Left column heading                  |
| left_body   | ❌       | string | Left column body text                |
| right_title | ✅       | string | Right column heading                 |
| right_body  | ❌       | string | Right column body text               |

---

### `quote`
**Purpose:** Big statement or testimonial on a dark background.
**Visual:** Night Navy background, large decorative quote mark, centered quote text, attribution.

| Field        | Required | Type   | Description                         |
|--------------|----------|--------|-------------------------------------|
| text         | ✅       | string | The quote text                      |
| attribution  | ❌       | string | Speaker name / source               |

---

### `metrics`
**Purpose:** Showcase key numbers/KPIs in card format with optional chart placeholder.
**Visual:** Light background (#F7F8FC), row of metric cards with accent top bars, chart area below.

| Field       | Required | Type     | Description                          |
|-------------|----------|----------|--------------------------------------|
| title       | ✅       | string   | Slide title                          |
| metrics     | ✅       | object[] | Array of `{"value": "...", "label": "..."}` |

Each metric object:
- `value` (string): The number/stat (e.g., "98%", "3.5x", "500+")
- `label` (string): Description of the metric

---

### `team`
**Purpose:** Showcase team members with avatar placeholders and bios.
**Visual:** White background, row of profile cards with colored avatar circles, name, role, bio.

| Field       | Required | Type     | Description                          |
|-------------|----------|----------|--------------------------------------|
| title       | ✅       | string   | Slide title (e.g., "Our Team")       |
| members     | ✅       | object[] | Array of member objects               |

Each member object:
- `name` (string): Person's name
- `role` (string): Job title
- `bio` (string, optional): Brief bio or expertise

---

### `case_study`
**Purpose:** Problem → Solution → Results layout for customer stories.
**Visual:** White background, three card columns (Challenge/Solution/Results) with accent-colored top bars and icon circles.

| Field       | Required | Type   | Description                          |
|-------------|----------|--------|--------------------------------------|
| title       | ✅       | string | Slide title (e.g., "Case Study: ...")  |
| challenge   | ✅       | string | The problem/challenge description    |
| solution    | ✅       | string | How it was solved                    |
| results     | ✅       | string | Outcomes and impact                  |

---

### `closing`
**Purpose:** Final slide with CTA, contact info, and branding.
**Visual:** Night Navy→Day Blue gradient background, decorative circles, large "Thank You" text, CTA button, contact info, white logo.

| Field       | Required | Type   | Description                          |
|-------------|----------|--------|--------------------------------------|
| title       | ✅       | string | Closing headline (e.g., "Thank You") |
| subtitle    | ❌       | string | Sub-message (e.g., "Questions?")     |
| contact     | ❌       | string | Contact info line                    |
| cta_text    | ❌       | string | Button text (default: "Contact Us")  |

---

### `blank`
**Purpose:** Empty slide for custom content or manual editing.
**Visual:** White background, logo only.

| Field       | Required | Type   | Description                          |
|-------------|----------|--------|--------------------------------------|
| (none)      | —        | —      | No fields required                   |

---

## Full Example Spec

```json
{
  "title": "OpenTeams Platform Overview",
  "slides": [
    {
      "type": "cover",
      "title": "OpenTeams Platform Overview",
      "subtitle": "Enterprise Open Source, Simplified",
      "date": "February 2026"
    },
    {
      "type": "agenda",
      "items": ["The Challenge", "Our Platform", "Key Features", "Results", "Next Steps"]
    },
    {
      "type": "content",
      "title": "The Open Source Challenge",
      "body": "Enterprises rely on thousands of open source packages.\nBut managing security, compliance, and support is complex.",
      "image_placeholder": "Diagram of open source dependency tree"
    },
    {
      "type": "two_column",
      "title": "Before & After OpenTeams",
      "left_title": "Before",
      "left_body": "Fragmented support\nNo SLA guarantees\nSecurity blind spots\nCompliance risk",
      "right_title": "After",
      "right_body": "Unified platform\nEnterprise SLAs\nProactive security\nFull compliance"
    },
    {
      "type": "metrics",
      "title": "Platform Impact",
      "metrics": [
        {"value": "99.9%", "label": "Uptime SLA"},
        {"value": "60%", "label": "Cost Reduction"},
        {"value": "10x", "label": "Faster Resolution"},
        {"value": "500+", "label": "Supported Packages"}
      ]
    },
    {
      "type": "quote",
      "text": "OpenTeams transformed how we manage\nopen source across the enterprise.",
      "attribution": "CTO, Fortune 500 Company"
    },
    {
      "type": "case_study",
      "title": "Case Study: Global Bank",
      "challenge": "Unmanaged open source dependencies across 200+ services.",
      "solution": "OpenTeams provided unified support, security scanning, and compliance tracking.",
      "results": "90% reduction in vulnerability response time. Full audit readiness."
    },
    {
      "type": "closing",
      "title": "Let's Get Started",
      "subtitle": "Ready to transform your open source strategy?",
      "contact": "hello@openteams.com  |  openteams.com"
    }
  ]
}
```
