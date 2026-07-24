#!/usr/bin/env python3
"""Verify Auchen Castle prototype: images, inquiry form, responsive nav."""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8772/index.html"
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
        page.evaluate("window.scrollTo({ top: 0, behavior: 'instant' })")
        page.wait_for_timeout(500)
        page.screenshot(path=str(ARTIFACTS / "auchen-desktop-hero.png"))

        page.locator("#inquiry").scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        event_date = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+21); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#eventDate").fill(event_date)
        page.locator("#delegateBand").select_option(label="51 to 75")
        page.locator("#eventType").select_option(label="Conference / meeting")
        page.locator("#packageInterest").select_option(label="Day Delegate (£45 pp)")
        page.locator("#inquiryForm button[type='submit']").click()
        page.wait_for_timeout(400)
        if not page.locator("#inquirySuccess.show").count():
            results["errors"].append("Inquiry success message did not show")
        results["interactions"].append("inquiry form filled and submitted (UI only)")

        for sel in ["#spaces", "#features", "#packages", "#gallery", "#location", "#contact"]:
            page.locator(sel).scroll_into_view_if_needed()
            page.wait_for_timeout(500)

        # Re-check images after scrolling so lazy-loaded assets are requested
        for sel in ["#spaces", "#gallery", "#location", "#contact"]:
            page.locator(sel).scroll_into_view_if_needed()
            page.wait_for_timeout(600)
        page.wait_for_timeout(1000)

        imgs = page.locator("img").all()
        for img in imgs:
            src = img.get_attribute("src") or ""
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            results["images"].append({"src": src, "ok": ok})
            if not ok:
                results["errors"].append(f"Broken image: {src}")

        page.evaluate("window.scrollTo({ top: 0, behavior: 'instant' })")
        page.wait_for_timeout(400)
        page.screenshot(
            path=str(ARTIFACTS / "auchen-desktop-full.png"), full_page=True
        )

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        if not page.locator("#navMobile.open").count():
            results["errors"].append("Mobile nav did not open")
        page.screenshot(path=str(ARTIFACTS / "auchen-mobile-menu.png"))
        page.locator("#navClose").click()
        page.wait_for_timeout(300)
        page.locator("#inquiry").scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        page.screenshot(path=str(ARTIFACTS / "auchen-mobile-inquiry.png"))
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(500)
        page.screenshot(
            path=str(ARTIFACTS / "auchen-mobile-full.png"), full_page=True
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
