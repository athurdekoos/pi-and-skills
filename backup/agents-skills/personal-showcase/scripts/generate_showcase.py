#!/usr/bin/env python3
"""
Generate a personal showcase HTML page with project cards and social links.

Usage:
    python3 generate_showcase.py --profile profile.json --out showcase.html
    python3 generate_showcase.py --profile profile.json --out showcase.html --theme dark
    python3 generate_showcase.py --profile profile.json --out showcase.html --theme glass
"""

import argparse
import json
import sys
import os
from pathlib import Path


# ── Social SVG Icons ──────────────────────────────────────────────────────────

ICONS = {
    "github": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>',
    "linkedin": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>',
    "discord": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M20.317 4.37a19.791 19.791 0 00-4.885-1.515.074.074 0 00-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 00-5.487 0 12.64 12.64 0 00-.617-1.25.077.077 0 00-.079-.037A19.736 19.736 0 003.677 4.37a.07.07 0 00-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 00.031.057 19.9 19.9 0 005.993 3.03.078.078 0 00.084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 00-.041-.106 13.107 13.107 0 01-1.872-.892.077.077 0 01-.008-.128 10.2 10.2 0 00.372-.292.074.074 0 01.077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 01.078.01c.12.098.246.198.373.292a.077.077 0 01-.006.127 12.299 12.299 0 01-1.873.892.077.077 0 00-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 00.084.028 19.839 19.839 0 006.002-3.03.077.077 0 00.032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 00-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/></svg>',
}

# ── Social Brand Colors ───────────────────────────────────────────────────────

SOCIAL_COLORS = {
    "github": "#333",
    "linkedin": "#0A66C2",
    "discord": "#5865F2",
}

# ── Theme Templates ───────────────────────────────────────────────────────────

def get_theme_css(theme, brand):
    """Return theme-specific CSS variables and overrides."""
    nn = brand["night_navy"]
    db = brand["day_blue"]
    sal = brand["salmon"]
    yel = brand["yellow"]
    grn = brand["accent_green"]

    themes = {
        "dark": f"""
            :root {{
                --bg-primary: {nn};
                --bg-secondary: #041b5e;
                --bg-card: rgba(77, 117, 254, 0.08);
                --bg-card-hover: rgba(77, 117, 254, 0.15);
                --text-primary: #ffffff;
                --text-secondary: rgba(255,255,255,0.7);
                --text-muted: rgba(255,255,255,0.45);
                --accent: {db};
                --accent-glow: rgba(77, 117, 254, 0.4);
                --salmon: {sal};
                --yellow: {yel};
                --green: {grn};
                --border: rgba(255,255,255,0.08);
                --shadow: 0 8px 32px rgba(0,0,0,0.4);
                --card-shadow: 0 4px 24px rgba(0,0,0,0.3);
            }}
        """,
        "light": f"""
            :root {{
                --bg-primary: #f8f9fc;
                --bg-secondary: #ffffff;
                --bg-card: #ffffff;
                --bg-card-hover: #f0f4ff;
                --text-primary: {nn};
                --text-secondary: #4a5568;
                --text-muted: #9ca3af;
                --accent: {db};
                --accent-glow: rgba(77, 117, 254, 0.15);
                --salmon: {sal};
                --yellow: {yel};
                --green: {grn};
                --border: rgba(2, 39, 145, 0.08);
                --shadow: 0 8px 32px rgba(2, 39, 145, 0.08);
                --card-shadow: 0 4px 24px rgba(2, 39, 145, 0.06);
            }}
        """,
        "glass": f"""
            :root {{
                --bg-primary: #0a0e27;
                --bg-secondary: #111640;
                --bg-card: rgba(255,255,255,0.04);
                --bg-card-hover: rgba(255,255,255,0.08);
                --text-primary: #ffffff;
                --text-secondary: rgba(255,255,255,0.65);
                --text-muted: rgba(255,255,255,0.35);
                --accent: {db};
                --accent-glow: rgba(77, 117, 254, 0.35);
                --salmon: {sal};
                --yellow: {yel};
                --green: {grn};
                --border: rgba(255,255,255,0.06);
                --shadow: 0 8px 32px rgba(0,0,0,0.5);
                --card-shadow: 0 4px 24px rgba(0,0,0,0.4);
            }}
            .card {{ backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); }}
            .social-btn {{ backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); }}
        """,
    }
    return themes.get(theme, themes["dark"])


def generate_html(profile, theme="dark"):
    """Generate the full HTML showcase page."""
    name = profile["name"]
    handle = profile["handle"]
    tagline = profile["tagline"]
    socials = profile["socials"]
    brand = profile["brand"]
    projects = profile["projects"]

    theme_css = get_theme_css(theme, brand)

    # Build social buttons
    social_html = ""
    for key, info in socials.items():
        icon_svg = ICONS.get(info["icon"], "")
        color = SOCIAL_COLORS.get(info["icon"], brand["day_blue"])
        social_html += f'''
        <a href="{info['url']}" target="_blank" rel="noopener" class="social-btn" data-color="{color}" title="{info['label']}">
            <span class="social-icon">{icon_svg}</span>
            <span class="social-label">{info['label']}</span>
        </a>'''

    # Build project cards
    project_html = ""
    for p in projects:
        tags_html = "".join(f'<span class="tag">{t}</span>' for t in p.get("tags", []))
        highlights_html = "".join(f"<li>{h}</li>" for h in p.get("highlights", []))
        repo_link = f'<a href="{p["repo"]}" target="_blank" rel="noopener" class="repo-link">View on GitHub →</a>' if p.get("repo") else ""

        project_html += f'''
        <div class="card project-card">
            <div class="card-header">
                <h3 class="card-title">{p["name"]}</h3>
                <div class="tags">{tags_html}</div>
            </div>
            <p class="card-desc">{p["description"]}</p>
            <ul class="highlights">{highlights_html}</ul>
            {repo_link}
        </div>'''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} — Showcase</title>
<style>
{theme_css}

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

@keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(24px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes glow {{
    0%, 100% {{ opacity: 0.6; }}
    50% {{ opacity: 1; }}
}}
@keyframes shimmer {{
    0% {{ background-position: -200% center; }}
    100% {{ background-position: 200% center; }}
}}
@keyframes float {{
    0%, 100% {{ transform: translateY(0); }}
    50% {{ transform: translateY(-8px); }}
}}
@keyframes orb-drift {{
    0%, 100% {{ transform: translate(0, 0) scale(1); }}
    33% {{ transform: translate(30px, -20px) scale(1.05); }}
    66% {{ transform: translate(-20px, 15px) scale(0.95); }}
}}

body {{
    font-family: 'Inter Tight', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    min-height: 100vh;
    overflow-x: hidden;
    position: relative;
}}

/* Ambient floating orbs */
.orb {{
    position: fixed;
    border-radius: 50%;
    filter: blur(80px);
    opacity: 0.15;
    animation: orb-drift 20s ease-in-out infinite;
    pointer-events: none;
    z-index: 0;
}}
.orb-1 {{ width: 400px; height: 400px; background: var(--accent); top: -100px; right: -100px; animation-delay: 0s; }}
.orb-2 {{ width: 300px; height: 300px; background: var(--salmon); bottom: -50px; left: -80px; animation-delay: -7s; }}
.orb-3 {{ width: 250px; height: 250px; background: var(--yellow); top: 50%; left: 60%; animation-delay: -13s; }}

.container {{
    max-width: 720px;
    margin: 0 auto;
    padding: 80px 24px 60px;
    position: relative;
    z-index: 1;
}}

/* ── Hero ── */
.hero {{
    text-align: center;
    margin-bottom: 56px;
    animation: fadeUp 0.8s ease-out;
}}
.avatar-ring {{
    width: 100px;
    height: 100px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--accent), var(--salmon), var(--yellow));
    padding: 3px;
    margin: 0 auto 24px;
    animation: glow 3s ease-in-out infinite;
}}
.avatar {{
    width: 100%;
    height: 100%;
    border-radius: 50%;
    background: var(--bg-primary);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 40px;
    font-weight: 700;
    color: var(--accent);
}}
.hero h1 {{
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    margin-bottom: 8px;
    background: linear-gradient(135deg, var(--text-primary) 0%, var(--accent) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.hero .handle {{
    font-size: 1rem;
    color: var(--accent);
    font-weight: 500;
    margin-bottom: 12px;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
}}
.hero .tagline {{
    font-size: 1.05rem;
    color: var(--text-secondary);
    max-width: 480px;
    margin: 0 auto;
    line-height: 1.6;
}}

/* ── Social Buttons ── */
.socials {{
    display: flex;
    gap: 14px;
    justify-content: center;
    margin: 32px 0 56px;
    animation: fadeUp 0.8s ease-out 0.15s both;
}}
.social-btn {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 22px;
    border-radius: 50px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    color: var(--text-primary);
    text-decoration: none;
    font-size: 0.9rem;
    font-weight: 600;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}}
.social-btn::before {{
    content: '';
    position: absolute;
    inset: 0;
    border-radius: 50px;
    opacity: 0;
    transition: opacity 0.3s;
}}
.social-btn:hover {{
    transform: translateY(-3px);
    box-shadow: 0 8px 25px var(--accent-glow);
    border-color: transparent;
}}
.social-btn:hover::before {{
    opacity: 1;
}}
.social-btn[data-color="#333"]:hover {{ background: #24292e; }}
.social-btn[data-color="#0A66C2"]:hover {{ background: #0A66C2; }}
.social-btn[data-color="#5865F2"]:hover {{ background: #5865F2; }}
.social-icon {{
    width: 20px;
    height: 20px;
    flex-shrink: 0;
}}
.social-icon svg {{
    width: 100%;
    height: 100%;
}}

/* ── Section ── */
.section {{
    margin-bottom: 48px;
    animation: fadeUp 0.8s ease-out 0.3s both;
}}
.section-label {{
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: var(--accent);
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 12px;
}}
.section-label::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}}

/* ── Cards ── */
.card {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 28px;
    margin-bottom: 16px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: var(--card-shadow);
}}
.card:hover {{
    background: var(--bg-card-hover);
    transform: translateY(-2px);
    box-shadow: var(--shadow);
    border-color: rgba(77, 117, 254, 0.2);
}}
.card-header {{
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 14px;
    flex-wrap: wrap;
}}
.card-title {{
    font-size: 1.25rem;
    font-weight: 700;
    letter-spacing: -0.02em;
}}
.tags {{
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
}}
.tag {{
    font-size: 0.7rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    background: var(--accent-glow);
    color: var(--accent);
    text-transform: lowercase;
    letter-spacing: 0.02em;
}}
.card-desc {{
    color: var(--text-secondary);
    line-height: 1.65;
    margin-bottom: 16px;
    font-size: 0.95rem;
}}
.highlights {{
    list-style: none;
    margin-bottom: 18px;
}}
.highlights li {{
    padding: 6px 0;
    padding-left: 20px;
    position: relative;
    color: var(--text-secondary);
    font-size: 0.9rem;
    line-height: 1.5;
}}
.highlights li::before {{
    content: '▸';
    position: absolute;
    left: 0;
    color: var(--accent);
    font-weight: 700;
}}
.repo-link {{
    display: inline-flex;
    align-items: center;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--accent);
    text-decoration: none;
    transition: all 0.2s;
    background: linear-gradient(90deg, var(--accent), var(--salmon));
    -webkit-background-clip: text;
    background-clip: text;
    background-size: 200% auto;
}}
.repo-link:hover {{
    animation: shimmer 2s linear infinite;
    -webkit-text-fill-color: transparent;
}}

/* ── Footer ── */
.footer {{
    text-align: center;
    padding-top: 40px;
    border-top: 1px solid var(--border);
    color: var(--text-muted);
    font-size: 0.8rem;
    animation: fadeUp 0.8s ease-out 0.45s both;
}}
.footer a {{
    color: var(--accent);
    text-decoration: none;
}}

/* ── Responsive ── */
@media (max-width: 540px) {{
    .container {{ padding: 48px 16px 40px; }}
    .hero h1 {{ font-size: 1.7rem; }}
    .socials {{ flex-direction: column; align-items: center; }}
    .card-header {{ flex-direction: column; }}
}}
</style>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
</head>
<body>

<div class="orb orb-1"></div>
<div class="orb orb-2"></div>
<div class="orb orb-3"></div>

<div class="container">
    <div class="hero">
        <div class="avatar-ring">
            <div class="avatar">{name[0]}</div>
        </div>
        <h1>{name}</h1>
        <div class="handle">@{handle}</div>
        <p class="tagline">{tagline}</p>
    </div>

    <div class="socials">
        {social_html}
    </div>

    <div class="section">
        <div class="section-label">Projects</div>
        {project_html}
    </div>

    <div class="footer">
        <p>Built with ✦ OpenTeams Brand Toolkit &middot; <a href="https://openteams.com">openteams.com</a></p>
    </div>
</div>

</body>
</html>'''

    return html


def main():
    parser = argparse.ArgumentParser(description="Generate a personal showcase HTML page")
    parser.add_argument("--profile", required=True, help="Path to profile.json")
    parser.add_argument("--out", required=True, help="Output HTML file path")
    parser.add_argument("--theme", default="dark", choices=["dark", "light", "glass"],
                        help="Visual theme (default: dark)")
    args = parser.parse_args()

    with open(args.profile) as f:
        profile = json.load(f)

    html = generate_html(profile, theme=args.theme)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as f:
        f.write(html)

    print(f"✅ Generated: {args.out}")
    print(f"   Theme: {args.theme}")
    print(f"   Projects: {len(profile['projects'])}")
    print(f"   Socials: {', '.join(profile['socials'].keys())}")


if __name__ == "__main__":
    main()
