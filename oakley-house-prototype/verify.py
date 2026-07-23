#!/usr/bin/env python3
"""Verify Oakley House prototype: images, nav, layout at multiple viewports."""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8767/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)

results = {"images": [], "interactions": [], "errors": []}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(1500)

        imgs = page.locator("img").all()
        for img in imgs:
            src = img.get_attribute("src") or ""
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            results["images"].append({"src": src, "ok": ok})
            if not ok:
                results["errors"].append(f"Broken image: {src}")

        brand = page.locator(".hero-brand").inner_text()
        h1 = page.locator(".hero h1").inner_text()
        results["interactions"].append(f"hero brand: {brand}")
        results["interactions"].append(f"hero h1: {h1}")

        for section in ["#spaces", "#amenities", "#grounds", "#packages", "#location", "#contact"]:
            page.locator(section).scroll_into_view_if_needed()
            page.wait_for_timeout(400)
            results["interactions"].append(f"scrolled to {section}")

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)
        page.screenshot(path=str(ARTIFACTS / "oakley-desktop-hero.png"))

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(600)
        page.screenshot(path=str(ARTIFACTS / "oakley-desktop-full.png"), full_page=True)

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(400)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        page.screenshot(path=str(ARTIFACTS / "oakley-mobile-menu.png"))
        page.locator("#navMobile a").first.click()
        page.wait_for_timeout(500)
        page.screenshot(path=str(ARTIFACTS / "oakley-mobile-full.png"), full_page=True)

        context.close()
        browser.close()

    out = ARTIFACTS / "oakley-verify.json"
    out.write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    if results["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
