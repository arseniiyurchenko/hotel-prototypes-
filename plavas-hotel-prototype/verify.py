#!/usr/bin/env python3
"""Verify prototype: images, booking widget, layout at multiple viewports."""

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
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=str(ARTIFACTS),
            record_video_size={"width": 1280, "height": 800},
        )
        page = context.new_page()

        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(1500)

        # Check all images
        imgs = page.locator("img").all()
        for i, img in enumerate(imgs):
            src = img.get_attribute("src") or ""
            ok = img.evaluate(
                "el => el.complete && el.naturalWidth > 0"
            )
            results["images"].append({"src": src, "ok": ok})
            if not ok:
                results["errors"].append(f"Broken image: {src}")

        # Booking widget — date pickers
        checkin = page.locator("#checkin")
        checkout = page.locator("#checkout")
        tomorrow = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+1); return d.toISOString().split('T')[0]; }"
        )
        day_after = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+3); return d.toISOString().split('T')[0]; }"
        )
        checkin.fill(tomorrow)
        checkout.fill(day_after)
        results["interactions"].append("date pickers filled")

        # Guest selector
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(300)
        page.locator("#adultsPlus").click()
        page.locator("#childrenPlus").click()
        summary = page.locator("#guestSummary").inner_text()
        results["interactions"].append(f"guest selector: {summary}")
        page.locator("#guestTrigger").click()

        # Scroll full page
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(800)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)

        # Desktop screenshot
        page.screenshot(path=str(ARTIFACTS / "desktop-full.png"), full_page=True)

        # Mobile viewport
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        page.screenshot(path=str(ARTIFACTS / "mobile-menu.png"))
        page.locator("#navClose").click()
        page.wait_for_timeout(300)

        page.locator("#guestTrigger").scroll_into_view_if_needed()
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(300)
        page.screenshot(path=str(ARTIFACTS / "mobile-booking.png"))

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(600)
        page.screenshot(path=str(ARTIFACTS / "mobile-full.png"), full_page=True)

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
