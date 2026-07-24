#!/usr/bin/env python3
"""Verify Cavendish Banqueting prototype: images, inquiry form, responsive nav."""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8771/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)

results = {"images": [], "interactions": [], "errors": []}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(2000)

        imgs = page.locator("img").all()
        for img in imgs:
            src = img.get_attribute("src") or ""
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            results["images"].append({"src": src, "ok": ok})
            if not ok:
                results["errors"].append(f"Broken image: {src}")

        page.locator("#inquiry").scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        tomorrow = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+14); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#eventDate").fill(tomorrow)
        page.locator("#guestBand").select_option(label="250 to 300")
        page.locator("#functionType").select_option(label="Wedding & Reception")
        page.locator("#dayBand").select_option(label="Fri – Sun")
        page.locator("#inquiryForm button[type='submit']").click()
        page.wait_for_timeout(500)
        results["interactions"].append("inquiry form filled and submitted (UI only)")

        for sel in ["#hall", "#features", "#gallery", "#location", "#contact"]:
            page.locator(sel).scroll_into_view_if_needed()
            page.wait_for_timeout(350)

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(400)
        page.screenshot(path=str(ARTIFACTS / "cavendish-desktop-hero.png"))
        page.screenshot(
            path=str(ARTIFACTS / "cavendish-desktop-full.png"), full_page=True
        )

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        if not page.locator("#navMobile.open").count():
            results["errors"].append("Mobile nav did not open")
        page.screenshot(path=str(ARTIFACTS / "cavendish-mobile-menu.png"))
        page.locator("#navClose").click()
        page.wait_for_timeout(300)
        page.locator("#inquiry").scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        page.screenshot(path=str(ARTIFACTS / "cavendish-mobile-inquiry.png"))
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(500)
        page.screenshot(
            path=str(ARTIFACTS / "cavendish-mobile-full.png"), full_page=True
        )

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
