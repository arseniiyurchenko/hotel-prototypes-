#!/usr/bin/env python3
"""Verify Miera Osta prototype: images, booking widget, smooth anchors, layout."""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8770/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)

results = {"images": [], "interactions": [], "scroll": [], "header": {}, "errors": []}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        page.goto(URL, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(2000)

        # Images
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
        results["header"] = {
            "logo_left": logo_box["x"] if logo_box else None,
            "cta_right_gap": (1280 - (cta_box["x"] + cta_box["width"])) if cta_box else None,
        }
        if not logo_box or logo_box["x"] < 28:
            results["errors"].append(f"Logo too close to left edge: {logo_box}")
        if not cta_box or (1280 - (cta_box["x"] + cta_box["width"])) < 28:
            results["errors"].append(f"CTA too close to right edge: {cta_box}")

        # Smooth scroll via nav anchors
        scroll_behavior = page.evaluate("() => getComputedStyle(document.documentElement).scrollBehavior")
        if scroll_behavior != "smooth":
            results["errors"].append(f"html scroll-behavior is '{scroll_behavior}', expected 'smooth'")

        for href in ["#rooms", "#amenities", "#gallery", "#location", "#trust", "#booking"]:
            before = page.evaluate("() => window.scrollY")
            page.locator(f'a.nav-desktop[href="{href}"], .nav-desktop a[href="{href}"]').first.click()
            page.wait_for_timeout(900)
            after = page.evaluate("() => window.scrollY")
            section_top = page.evaluate(
                f"() => document.querySelector('{href}').getBoundingClientRect().top"
            )
            results["scroll"].append({"href": href, "before": before, "after": after, "sectionTop": section_top})
            # Section should be near viewport top after scroll
            if abs(section_top) > 140:
                results["errors"].append(f"Anchor {href} did not land near section (top={section_top})")

        # Booking widget
        tomorrow = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+2); return d.toISOString().split('T')[0]; }"
        )
        day_after = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+5); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#checkin").fill(tomorrow)
        page.locator("#checkout").fill(day_after)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(300)
        if not page.locator("#guestPanel.open").count():
            results["errors"].append("Guest panel did not open")
        page.locator("#adultsPlus").click()
        page.locator("#childrenPlus").click()
        summary = page.locator("#guestSummary").inner_text()
        results["interactions"].append(f"guest selector: {summary}")
        page.locator("#roomType").select_option("family")
        page.locator("#searchBtn").click()
        page.wait_for_timeout(400)

        page.screenshot(path=str(ARTIFACTS / "miera-osta-desktop.png"), full_page=True)

        # Mobile
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.evaluate("window.scrollTo(0, 0)")
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        if not page.locator("#navMobile.open").count():
            results["errors"].append("Mobile nav did not open")
        page.screenshot(path=str(ARTIFACTS / "miera-osta-mobile-menu.png"))
        page.locator("#navClose").click()
        page.wait_for_timeout(300)

        # Mobile header spacing
        logo_box_m = page.locator(".logo").bounding_box()
        toggle_box = page.locator("#menuToggle").bounding_box()
        if not logo_box_m or logo_box_m["x"] < 24:
            results["errors"].append(f"Mobile logo cramped: {logo_box_m}")
        if not toggle_box or (390 - (toggle_box["x"] + toggle_box["width"])) < 24:
            results["errors"].append(f"Mobile toggle cramped: {toggle_box}")

        page.locator("#guestTrigger").scroll_into_view_if_needed()
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(300)
        page.screenshot(path=str(ARTIFACTS / "miera-osta-mobile-booking.png"))
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(500)
        page.screenshot(path=str(ARTIFACTS / "miera-osta-mobile-full.png"), full_page=True)

        context.close()
        browser.close()

    print(json.dumps(results, indent=2))
    broken = [r for r in results["images"] if not r["ok"]]
    print(f"\nImages: {len(results['images'])} total, {len(broken)} broken")
    if results["errors"]:
        print("ERRORS:", results["errors"])
        sys.exit(1)
    print("Verification passed.")


if __name__ == "__main__":
    main()
