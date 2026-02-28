#!/usr/bin/env python3
"""
Refresh website_cues in brand.json by crawling openteams.com.

Usage:
  python refresh_site_style.py --url https://openteams.com/ --brand-json ../references/brand.json
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from typing import Any, Dict, List
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("refresh_site_style")

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("Missing dependencies. Run: pip install requests beautifulsoup4 lxml")


def _is_same_origin(candidate_url: str, origin_url: str) -> bool:
    """Return True if candidate_url shares the same hostname as origin_url."""
    try:
        return urlparse(candidate_url).hostname == urlparse(origin_url).hostname
    except Exception:
        return False


def crawl_website(url: str) -> Dict[str, Any]:
    """Fetch homepage + a few pages, extract CSS-derived style tokens."""
    pages_to_fetch = [url]

    # Try sitemap
    try:
        r = requests.get(url.rstrip("/") + "/sitemap.xml", timeout=10)
        if r.status_code == 200 and "xml" in r.headers.get("content-type", ""):
            soup = BeautifulSoup(r.text, "lxml-xml")
            locs = [loc.text for loc in soup.find_all("loc")]
            # Only follow same-origin links to prevent SSRF
            candidates = [u for u in locs
                          if _is_same_origin(u, url) and
                          any(k in u.lower() for k in
                          ("product", "feature", "solution", "platform", "about"))]
            pages_to_fetch.extend(candidates[:3])
    except Exception as e:
        log.debug(f"Sitemap fetch failed: {e}")

    pages_to_fetch = list(dict.fromkeys(pages_to_fetch))

    extracted_css_vars: Dict[str, str] = {}
    radii: List[int] = []
    shadows: List[str] = []
    bg_colors: List[str] = []

    for page_url in pages_to_fetch[:4]:
        try:
            log.info(f"Crawling {page_url} ...")
            resp = requests.get(page_url, timeout=15, headers={
                "User-Agent": "OpenTeams-BrandBot/1.0 (template builder)"
            })
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")

            for tag in soup.find_all("style"):
                text = tag.string or ""
                for m in re.finditer(r'--([\w-]+)\s*:\s*([^;]+);', text):
                    extracted_css_vars[m.group(1)] = m.group(2).strip()
                for m in re.finditer(r'border-radius\s*:\s*(\d+)', text):
                    radii.append(int(m.group(1)))
                for m in re.finditer(r'box-shadow\s*:\s*([^;]+);', text):
                    shadows.append(m.group(1).strip())
                for m in re.finditer(r'background(?:-color)?\s*:\s*(#[0-9a-fA-F]{3,8}|rgb[^;]+)', text):
                    bg_colors.append(m.group(1).strip())

            for link in soup.find_all("link", rel="stylesheet")[:2]:
                href = link.get("href", "")
                if not href:
                    continue
                if href.startswith("/"):
                    href = url.rstrip("/") + href
                elif not href.startswith("http"):
                    href = url.rstrip("/") + "/" + href
                if not _is_same_origin(href, url):
                    continue
                try:
                    css_resp = requests.get(href, timeout=10)
                    content_type = css_resp.headers.get("content-type", "")
                    if css_resp.status_code == 200 and "text/" in content_type:
                        css_text = css_resp.text[:200_000]
                        for m in re.finditer(r'--([\w-]+)\s*:\s*([^;]+);', css_text):
                            extracted_css_vars[m.group(1)] = m.group(2).strip()
                        for m in re.finditer(r'border-radius\s*:\s*(\d+)', css_text):
                            radii.append(int(m.group(1)))
                        for m in re.finditer(r'box-shadow\s*:\s*([^;]+);', css_text):
                            shadows.append(m.group(1).strip())
                except Exception:
                    pass

        except Exception as e:
            log.warning(f"Failed to crawl {page_url}: {e}")

    # Build updated cues
    cues: Dict[str, Any] = {}

    if radii:
        common_radius = max(set(radii), key=radii.count)
        cues["card_radius_px"] = common_radius
        log.info(f"Derived card radius: {common_radius}px")

    if shadows:
        cues["card_shadow_sample"] = shadows[0][:100]
        log.info(f"Derived card shadow: {shadows[0][:60]}...")

    if bg_colors:
        white_like = sum(1 for c in bg_colors if c.upper() in ("#FFF", "#FFFFFF", "#FAFAFA", "#F9FAFB"))
        cues["white_dominant"] = (white_like / max(len(bg_colors), 1)) > 0.4

    cues["css_variables_found"] = len(extracted_css_vars)
    cues["pages_crawled"] = len(pages_to_fetch)

    log.info(f"Crawl complete — {len(extracted_css_vars)} CSS vars, "
             f"{len(radii)} radii, {len(shadows)} shadows extracted.")

    return cues


def main():
    parser = argparse.ArgumentParser(description="Refresh website style cues in brand.json")
    parser.add_argument("--url", default="https://openteams.com/",
                        help="Website URL to crawl")
    parser.add_argument("--brand-json", required=True,
                        help="Path to brand.json to update")

    args = parser.parse_args()

    # Load existing brand.json
    with open(args.brand_json) as f:
        brand = json.load(f)

    old_cues = brand.get("website_cues", {})

    # Crawl and get new cues
    new_cues = crawl_website(args.url)

    # Merge: new values override, but keep existing keys not in new
    merged = dict(old_cues)
    merged.update(new_cues)

    brand["website_cues"] = merged

    # Save
    with open(args.brand_json, "w") as f:
        json.dump(brand, f, indent=2)

    # Print diff summary
    print("\n--- Website Cues Update Summary ---")
    for key in sorted(set(list(old_cues.keys()) + list(new_cues.keys()))):
        old_val = old_cues.get(key, "(new)")
        new_val = merged.get(key)
        if key in new_cues and str(old_val) != str(new_val):
            print(f"  UPDATED  {key}: {old_val} → {new_val}")
        elif key in new_cues:
            print(f"  SAME     {key}: {new_val}")
        else:
            print(f"  KEPT     {key}: {new_val}")

    print(f"\nSaved → {args.brand_json}")


if __name__ == "__main__":
    main()
