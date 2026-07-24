#!/usr/bin/env python3
"""Verify Lingnerschloss prototype: images, inquiry form, desktop/mobile layout."""

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

        # Force lazy images into view so they load before checks
        page.evaluate(
            """async () => {
              const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
              const h = document.body.scrollHeight;
              for (let y = 0; y < h; y += 500) {
                window.scrollTo(0, y);
                await sleep(200);
              }
              window.scrollTo(0, 0);
              await sleep(400);
              for (const img of document.images) {
                if ('loading' in img) img.loading = 'eager';
              }
            }"""
        )
        page.wait_for_timeout(2500)

        imgs = page.locator("img").all()
        for img in imgs:
            src = img.get_attribute("src") or ""
            img.scroll_into_view_if_needed()
            page.wait_for_timeout(150)
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            if not ok:
                page.wait_for_timeout(800)
                ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            results["images"].append({"src": src[:120], "ok": ok})
            if not ok:
                results["errors"].append(f"Broken image: {src}")

        brand = page.locator(".hero-brand").inner_text().strip()
        tagline = page.locator(".hero-tagline").inner_text().strip()
        results["interactions"].append(f"hero brand: {brand}")
        results["interactions"].append(f"hero tagline: {tagline}")
        if "lingnerschloss" not in brand.lower():
            results["errors"].append("Hero brand missing Lingnerschloss")
        if "tradition" not in tagline.lower():
            results["errors"].append("Tagline missing expected text")

        page.locator("#inquiry").scroll_into_view_if_needed()
        page.locator("#name").fill("Prototype Guest")
        page.locator("#email").fill("guest@example.com")
        page.locator("#option").select_option(label="Wedding")
        page.locator("#request").fill("Inquiry about Sternensaal")
        page.locator("#inquiryForm button[type=submit]").click()
        page.wait_for_timeout(400)
        if page.locator("#formSuccess.show").count() == 0:
            results["errors"].append("Form success message not shown")
        else:
            results["interactions"].append("inquiry form submitted (prototype)")

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)
        page.screenshot(path=str(ARTIFACTS / "lingnerschloss-desktop-hero.png"))

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(800)
        page.screenshot(path=str(ARTIFACTS / "lingnerschloss-desktop-full.png"), full_page=True)

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.evaluate("window.scrollTo(0, 0)")
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        page.screenshot(path=str(ARTIFACTS / "lingnerschloss-mobile-menu.png"))
        page.locator("#navClose").click()
        page.wait_for_timeout(300)

        page.locator("#spaces").scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        page.screenshot(path=str(ARTIFACTS / "lingnerschloss-mobile-spaces.png"))

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(600)
        page.screenshot(path=str(ARTIFACTS / "lingnerschloss-mobile-full.png"), full_page=True)

        context.close()
        browser.close()

    out = ARTIFACTS / "lingnerschloss-verify.json"
    out.write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    if results["errors"]:
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()
