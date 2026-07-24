#!/usr/bin/env python3
"""Verify Albert Hall prototype: images, booking widget, smooth scroll, layout."""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8777/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)

results = {"images": [], "interactions": [], "smooth_scroll": None, "header_spacing": None, "errors": []}


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

        header_box = page.locator(".header-inner").bounding_box()
        logo_box = page.locator(".logo").bounding_box()
        cta_box = page.locator(".header-cta").bounding_box()
        if header_box and logo_box and cta_box:
            left_pad = logo_box["x"] - header_box["x"]
            right_pad = (header_box["x"] + header_box["width"]) - (cta_box["x"] + cta_box["width"])
            results["header_spacing"] = {"left_pad": round(left_pad, 1), "right_pad": round(right_pad, 1)}
            if left_pad < 16 or right_pad < 16:
                results["errors"].append(f"Header spacing too tight: left={left_pad:.0f}px right={right_pad:.0f}px")

        start_y = page.evaluate("window.scrollY")
        page.locator('.nav-desktop a[href="#spaces"]').click()
        page.wait_for_timeout(1200)
        end_y = page.evaluate("window.scrollY")
        spaces_top = page.locator("#spaces").evaluate("el => el.getBoundingClientRect().top")
        results["smooth_scroll"] = {
            "scrolled": end_y > start_y + 100,
            "spaces_near_top": abs(spaces_top) < 120,
        }
        if end_y <= start_y + 50:
            results["errors"].append("Anchor navigation did not scroll")

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)

        tomorrow = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+14); return d.toISOString().split('T')[0]; }"
        )
        alt = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+21); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#eventDate").fill(tomorrow)
        page.locator("#altDate").fill(alt)
        results["interactions"].append("date pickers filled")

        page.locator("#guestTrigger").click()
        page.wait_for_timeout(300)
        page.locator("#guestsPlus").click()
        summary = page.locator("#guestSummary").inner_text()
        results["interactions"].append(f"guest selector: {summary}")

        page.locator("#spaceType").select_option("osborne-suite")
        results["interactions"].append("space selector changed")

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(800)
        page.screenshot(path=str(ARTIFACTS / "albert-hall-desktop-full.png"), full_page=True)

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        page.screenshot(path=str(ARTIFACTS / "albert-hall-mobile-menu.png"))
        page.locator("#navClose").click()
        page.wait_for_timeout(300)

        page.locator("#guestTrigger").scroll_into_view_if_needed()
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(300)
        page.screenshot(path=str(ARTIFACTS / "albert-hall-mobile-booking.png"))

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(600)
        page.screenshot(path=str(ARTIFACTS / "albert-hall-mobile-full.png"), full_page=True)

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
