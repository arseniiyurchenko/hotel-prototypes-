#!/usr/bin/env python3
"""Verify Szent Adalbert venue prototype: images, inquiry UI, desktop + mobile."""

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

        page.locator("#eventDate").fill("2026-09-12")
        page.locator("#eventType").select_option("wedding")
        page.locator("#guests").select_option("151-400")
        page.locator("#spacePref").select_option("banquet")
        page.locator("#inquirySubmit").click()
        page.wait_for_timeout(600)
        status = page.locator("#formStatus").inner_text()
        results["interactions"].append(f"inquiry CTA: {status[:80]}")

        for sel in ["#spaces", "#amenities", "#weddings", "#gallery", "#location", "#enquiry"]:
            page.locator(sel).scroll_into_view_if_needed()
            page.wait_for_timeout(350)

        page.locator("#name").fill("Demo Guest")
        page.locator("#email").fill("demo@example.com")
        page.locator("#enquirySubmit").click()
        page.wait_for_timeout(400)
        results["interactions"].append(page.locator("#formStatus").inner_text()[:90])

        page.screenshot(path=str(ARTIFACTS / "szent-adalbert-desktop-full.png"), full_page=True)

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.evaluate("window.scrollTo(0, 0)")
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        if not page.locator("#navMobile.open").count():
            results["errors"].append("Mobile nav did not open")
        page.screenshot(path=str(ARTIFACTS / "szent-adalbert-mobile-menu.png"))
        page.locator("#navClose").click()
        page.wait_for_timeout(300)

        page.locator("#inquiry").scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        page.screenshot(path=str(ARTIFACTS / "szent-adalbert-mobile-inquiry.png"))

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(600)
        page.screenshot(path=str(ARTIFACTS / "szent-adalbert-mobile-full.png"), full_page=True)

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
