"""Render docs/guide.html to docs/Job-Search-OS-Setup-Guide.pdf.

Uses headless Chromium via Playwright (installed by scripts/install_deps.sh).
Run from the repo root:

    python3 docs/generate_pdf.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HTML_PATH = HERE / "guide.html"
PDF_PATH = HERE / "Job-Search-OS-Setup-Guide.pdf"


async def render() -> None:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Install playwright first: pip install playwright && playwright install chromium")
        sys.exit(1)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context()
        page = await ctx.new_page()
        await page.goto(HTML_PATH.as_uri())
        await page.wait_for_load_state("networkidle")
        await page.pdf(
            path=str(PDF_PATH),
            format="A4",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            prefer_css_page_size=True,
        )
        await browser.close()
    print(f"Wrote {PDF_PATH}")


if __name__ == "__main__":
    asyncio.run(render())
