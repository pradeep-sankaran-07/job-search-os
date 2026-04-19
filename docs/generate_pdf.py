"""Render docs/guide.html to docs/Job-Search-OS-Setup-Guide.pdf.

Uses headless Chromium via Playwright (installed by scripts/install_deps.sh).
A persistent footer — "Built by Pradeep Sankaran · LinkedIn" — is rendered
at the bottom of every page using Playwright's footer template.

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

# Footer shown on every page. Playwright injects this into a margin box at
# the bottom of each page. Styles must be inline — external CSS does not
# apply to header/footer templates.
FOOTER_TEMPLATE = """
<div style="
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  font-size: 8.5pt;
  color: #6e6e73;
  width: 100%;
  padding: 0 14mm;
  box-sizing: border-box;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 0.5pt solid #d2d2d7;
  padding-top: 3mm;
">
  <span>Built by Pradeep Sankaran</span>
  <span>Questions? <span style="color:#1d1d1f;font-weight:600;">linkedin.com/in/pradeep-sankaran</span></span>
</div>
"""

# Empty header — Playwright requires displayHeaderFooter: true and renders
# both; pass a blank div to suppress the default date/title header.
HEADER_TEMPLATE = "<div></div>"


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
            display_header_footer=True,
            header_template=HEADER_TEMPLATE,
            footer_template=FOOTER_TEMPLATE,
            # Leave room for the footer at the bottom of every page.
            margin={"top": "0", "right": "0", "bottom": "14mm", "left": "0"},
        )
        await browser.close()
    print(f"Wrote {PDF_PATH}")


if __name__ == "__main__":
    asyncio.run(render())
