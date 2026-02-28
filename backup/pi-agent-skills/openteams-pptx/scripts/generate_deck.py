#!/usr/bin/env python3
"""
OpenTeams PPTX Generator — CLI entry point.

Usage:
  python generate_deck.py --spec slides.json --brand ../references/brand.json --out output.pptx
  echo '{"slides":[...]}' | python generate_deck.py --brand ../references/brand.json --out output.pptx
  python generate_deck.py --demo --brand ../references/brand.json --out demo.pptx
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import os
import textwrap

# Ensure same-directory imports work when invoked as a script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pptx import Presentation
from pptx.util import Inches, Emu

from brand_engine import load_brand, build_theme
from slide_builder import SlideBuilder
from slide_renderers import RENDERERS

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("generate_deck")


# ---------------------------------------------------------------------------
# Spec validation
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = {
    "cover":           ["title"],
    "section_divider": ["title"],
    "agenda":          ["items"],
    "content":         ["title"],
    "two_column":      ["title", "left_title", "right_title"],
    "quote":           ["text"],
    "metrics":         ["title", "metrics"],
    "team":            ["title", "members"],
    "case_study":      ["title", "challenge", "solution", "results"],
    "closing":         ["title"],
    "blank":           [],
}


def validate_spec(spec: dict) -> list[str]:
    """Return a list of human-readable error strings. Empty list = valid."""
    errors = []
    if "slides" not in spec or not isinstance(spec["slides"], list):
        return ["Spec must contain a 'slides' array."]
    for i, slide in enumerate(spec["slides"], 1):
        stype = slide.get("type")
        if not stype:
            errors.append(f"Slide {i}: missing 'type' field.")
            continue
        if stype not in REQUIRED_FIELDS:
            errors.append(f"Slide {i}: unknown type '{stype}'. "
                          f"Valid types: {', '.join(REQUIRED_FIELDS)}")
            continue
        for field in REQUIRED_FIELDS[stype]:
            if field not in slide:
                errors.append(f"Slide {i} ({stype}): missing required field '{field}'.")
    return errors


# ---------------------------------------------------------------------------
# Demo spec (reproduces the 10-slide template from build_template.py)
# ---------------------------------------------------------------------------

DEMO_SPEC = {
    "title": "OpenTeams_Template_Demo",
    "slides": [
        {
            "type": "cover",
            "title": "Presentation Title",
            "subtitle": "Subtitle or tagline goes here",
            "date": "Month Year"
        },
        {
            "type": "section_divider",
            "title": "Section Title",
            "subtitle": "Brief description of this section"
        },
        {
            "type": "agenda",
            "items": [
                "Introduction & Context",
                "Problem Statement",
                "Our Approach & Solution",
                "Key Results & Metrics",
                "Next Steps & Discussion"
            ]
        },
        {
            "type": "content",
            "title": "Content Slide Title",
            "body": "Add your key points here. The template uses generous whitespace\nand brand-consistent typography for a clean, modern look.\n\nUse this layout for text-heavy slides that need a supporting visual.",
            "image_placeholder": "Visual / Image"
        },
        {
            "type": "two_column",
            "title": "Two-Column Layout",
            "left_title": "Left Column",
            "left_body": "Supporting text for the first column. Use for\ncomparisons, features, or parallel content.",
            "right_title": "Right Column",
            "right_body": "Supporting text for the second column.\nMaintain visual balance between columns."
        },
        {
            "type": "quote",
            "text": "A bold statement that captures\nyour key message in one line.",
            "attribution": "Speaker Name, Title"
        },
        {
            "type": "metrics",
            "title": "Key Metrics",
            "metrics": [
                {"value": "98%", "label": "Customer Satisfaction"},
                {"value": "3.5x", "label": "ROI Improvement"},
                {"value": "500+", "label": "Active Projects"},
                {"value": "24/7", "label": "Global Support"}
            ]
        },
        {
            "type": "team",
            "title": "Our Team",
            "members": [
                {"name": "Team Member 1", "role": "Role / Title", "bio": "Brief bio or expertise\narea description."},
                {"name": "Team Member 2", "role": "Role / Title", "bio": "Brief bio or expertise\narea description."},
                {"name": "Team Member 3", "role": "Role / Title", "bio": "Brief bio or expertise\narea description."},
                {"name": "Team Member 4", "role": "Role / Title", "bio": "Brief bio or expertise\narea description."}
            ]
        },
        {
            "type": "case_study",
            "title": "Case Study: Client Name",
            "challenge": "Describe the client's\nchallenge or pain point\nthat needed addressing.",
            "solution": "Explain the OpenTeams\napproach and how the\nsolution was implemented.",
            "results": "Share quantifiable\noutcomes and the\nimpact delivered."
        },
        {
            "type": "closing",
            "title": "Thank You",
            "subtitle": "Questions? Let's discuss.",
            "contact": "hello@openteams.com  |  openteams.com",
            "cta_text": "Contact Us"
        }
    ]
}


# ---------------------------------------------------------------------------
# Main generation logic
# ---------------------------------------------------------------------------

def generate(spec: dict, brand_json_path: str, output_path: str) -> None:
    """Generate a .pptx file from a slide spec and brand config."""
    # Validate spec
    errors = validate_spec(spec)
    if errors:
        print("❌ Spec validation failed:", file=sys.stderr)
        for err in errors:
            print(f"   • {err}", file=sys.stderr)
        sys.exit(1)

    # Load brand and build theme
    log.info("Loading brand config...")
    brand = load_brand(brand_json_path)
    theme = build_theme(brand)

    # Create presentation
    prs = Presentation()
    prs.slide_width = Emu(int(Inches(theme.slide_width_inches)))
    prs.slide_height = Emu(int(Inches(theme.slide_height_inches)))

    sb = SlideBuilder(prs, theme)

    # Render slides
    for i, slide_spec in enumerate(spec["slides"], 1):
        stype = slide_spec["type"]
        renderer = RENDERERS.get(stype)
        if renderer is None:
            log.error(f"Slide {i}: unknown type '{stype}' — skipping.")
            continue
        try:
            renderer(sb, slide_spec)
            log.info(f"  ✓ Slide {i}: {stype}")
        except Exception as e:
            log.error(f"  ✗ Slide {i} ({stype}): {e}")
            import traceback
            traceback.print_exc()

    # Save
    prs.save(output_path)
    log.info(f"\n{'=' * 50}")
    log.info(f"Generated {len(prs.slides)} slides → {output_path}")
    log.info(f"{'=' * 50}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="OpenTeams PPTX Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python generate_deck.py --spec slides.json --brand ../references/brand.json --out deck.pptx
              python generate_deck.py --demo --brand ../references/brand.json --out demo.pptx
        """)
    )
    parser.add_argument("--spec", help="Path to slide spec JSON file")
    parser.add_argument("--brand", required=True, help="Path to brand.json")
    parser.add_argument("--out", required=True, help="Output .pptx file path")
    parser.add_argument("--demo", action="store_true",
                        help="Generate demo deck with all slide types")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable debug logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.demo:
        spec = DEMO_SPEC
    elif args.spec:
        with open(args.spec) as f:
            spec = json.load(f)
    elif not sys.stdin.isatty():
        spec = json.load(sys.stdin)
    else:
        parser.error("Provide --spec <file>, --demo, or pipe JSON to stdin.")

    generate(spec, args.brand, args.out)


if __name__ == "__main__":
    main()
