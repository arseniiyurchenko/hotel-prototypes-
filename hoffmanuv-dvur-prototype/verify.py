#!/usr/bin/env python3
"""Verify Hoffmanův dvůr prototype: images, inquiry form, layout."""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/index.html"
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

        for sel in ["#prostory", "#akce", "#sluzby", "#galerie", "#reference", "#kontakt"]:
            page.locator(sel).scroll_into_view_if_needed()
            page.wait_for_timeout(700)

        # Ensure lazy-loaded images have time to fetch after scroll
        page.locator("#galerie").scroll_into_view_if_needed()
        page.wait_for_function(
            "() => [...document.images].every(img => img.complete && img.naturalWidth > 0)",
            timeout=20000,
        )

        imgs = page.locator("img").all()
        for img in imgs:
            src = img.get_attribute("src") or ""
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            results["images"].append({"src": src, "ok": ok})
            if not ok:
                results["errors"].append(f"Broken image: {src}")

        page.locator("#kontakt").scroll_into_view_if_needed()
        page.locator("#name").fill("Test Host")
        page.locator("#email").fill("test@example.com")
        page.locator("#eventType").select_option("svatba")
        page.locator("#inquiryForm button[type=submit]").click()
        page.wait_for_timeout(400)
        if not page.locator("#formStatus.show").count():
            results["errors"].append("Inquiry form status did not show")
        else:
            results["interactions"].append("inquiry form submitted (prototype)")

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(400)
        page.locator(".hero").screenshot(path=str(ARTIFACTS / "hoffman-hero.png"))
        page.screenshot(path=str(ARTIFACTS / "hoffman-desktop-full.png"), full_page=True)

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        if not page.locator("#navMobile.open").count():
            results["errors"].append("Mobile nav did not open")
        page.screenshot(path=str(ARTIFACTS / "hoffman-mobile-menu.png"))
        page.locator("#navClose").click()
        page.wait_for_timeout(300)
        page.screenshot(path=str(ARTIFACTS / "hoffman-mobile-full.png"), full_page=True)

        context.close()
        browser.close()

    broken = [r for r in results["images"] if not r["ok"]]
    print(json.dumps(results, indent=2))
    print(f"\nImages: {len(results['images'])} total, {len(broken)} broken")
    if results["errors"]:
        print("ERRORS:", results["errors"])
        sys.exit(1)
    print("Verification passed.")


if __name__ == "__main__":
    main()
