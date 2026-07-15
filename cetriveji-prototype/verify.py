#!/usr/bin/env python3
"""Verify Četri Vēji prototype: images, booking widget, anchors, layout."""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8771/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)

results = {"images": [], "interactions": [], "layout": {}, "errors": []}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        page.goto(URL, wait_until="networkidle", timeout=120000)
        page.wait_for_timeout(2000)

        # Image load check
        imgs = page.locator("img").all()
        for img in imgs:
            src = img.get_attribute("src") or ""
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            results["images"].append({"src": src, "ok": ok})
            if not ok:
                results["errors"].append(f"Broken image: {src}")

        # Header spacing from corners
        logo_box = page.locator(".logo").bounding_box()
        cta_box = page.locator(".header-cta").bounding_box()
        if logo_box:
            results["layout"]["logo_left"] = logo_box["x"]
            if logo_box["x"] < 28:
                results["errors"].append(f"Logo too close to left edge: {logo_box['x']:.1f}px")
        if cta_box:
            right_gap = 1280 - (cta_box["x"] + cta_box["width"])
            results["layout"]["cta_right_gap"] = right_gap
            if right_gap < 28:
                results["errors"].append(f"CTA too close to right edge: {right_gap:.1f}px")

        # Smooth scroll via nav anchor
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(400)
        scroll_behavior = page.evaluate(
            "() => getComputedStyle(document.documentElement).scrollBehavior"
        )
        results["layout"]["scroll_behavior"] = scroll_behavior
        if scroll_behavior != "smooth":
            results["errors"].append(f"scroll-behavior is '{scroll_behavior}', expected 'smooth'")

        y_before = page.evaluate("() => window.scrollY")
        page.locator('.nav-desktop a[href="#rooms"]').click()
        page.wait_for_timeout(900)
        y_mid = page.evaluate("() => window.scrollY")
        page.wait_for_timeout(700)
        y_after = page.evaluate("() => window.scrollY")
        results["interactions"].append(
            f"anchor #rooms scroll: {y_before} -> {y_mid} -> {y_after}"
        )
        if y_after < 200:
            results["errors"].append("Nav anchor to #rooms did not scroll the page")

        # Booking widget
        tomorrow = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+2); return d.toISOString().split('T')[0]; }"
        )
        checkout_day = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+5); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#checkin").fill(tomorrow)
        page.locator("#checkout").fill(checkout_day)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(300)
        if not page.locator("#guestPanel.open").count():
            results["errors"].append("Guest panel did not open")
        page.locator("#adultsPlus").click()
        page.locator("#childrenPlus").click()
        summary = page.locator("#guestSummary").inner_text()
        results["interactions"].append(f"guest selector: {summary}")
        page.locator("#roomType").select_option("apartamenti")
        page.mouse.click(200, 200)
        page.wait_for_timeout(200)

        for sel in ["#amenities", "#gallery", "#location", "#trust", "#footer"]:
            page.locator(sel).scroll_into_view_if_needed()
            page.wait_for_timeout(250)

        page.screenshot(path=str(ARTIFACTS / "cetriveji-desktop-full.png"), full_page=True)

        # Mobile
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(300)
        logo_m = page.locator(".logo").bounding_box()
        toggle_m = page.locator("#menuToggle").bounding_box()
        if logo_m and logo_m["x"] < 24:
            results["errors"].append(f"Mobile logo too close to edge: {logo_m['x']:.1f}px")
        if toggle_m:
            right_gap_m = 390 - (toggle_m["x"] + toggle_m["width"])
            results["layout"]["mobile_toggle_right_gap"] = right_gap_m
            if right_gap_m < 24:
                results["errors"].append(f"Mobile toggle too close to edge: {right_gap_m:.1f}px")

        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        if not page.locator("#navMobile.open").count():
            results["errors"].append("Mobile nav did not open")
        page.screenshot(path=str(ARTIFACTS / "cetriveji-mobile-menu.png"))
        page.locator("#navClose").click()
        page.wait_for_timeout(300)

        page.locator("#guestTrigger").scroll_into_view_if_needed()
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(300)
        page.screenshot(path=str(ARTIFACTS / "cetriveji-mobile-booking.png"))
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(500)
        page.screenshot(path=str(ARTIFACTS / "cetriveji-mobile-full.png"), full_page=True)

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
