#!/usr/bin/env python3
"""Verify Hotel Madona prototype: images, widget, smooth scroll, header spacing."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)


def main():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(URL, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(2000)

        imgs = page.locator("img").all()
        for i, img in enumerate(imgs):
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            src = img.get_attribute("src") or ""
            if not ok:
                errors.append(f"Broken image [{i}]: {src}")

        # Header spacing from corners
        logo_box = page.locator(".logo").bounding_box()
        cta_box = page.locator(".header-cta").bounding_box()
        if not logo_box or logo_box["x"] < 28:
            errors.append(f"Logo too close to left edge: {logo_box}")
        if not cta_box or (1280 - (cta_box["x"] + cta_box["width"])) < 28:
            errors.append(f"CTA too close to right edge: {cta_box}")

        # Smooth scroll via nav
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(300)
        behavior = page.evaluate("() => getComputedStyle(document.documentElement).scrollBehavior")
        if behavior != "smooth":
            errors.append(f"html scroll-behavior is '{behavior}', expected 'smooth'")

        page.locator('.nav-desktop a[href="#rooms"]').click()
        page.wait_for_timeout(900)
        y1 = page.evaluate("() => window.scrollY")
        if y1 < 200:
            errors.append(f"Nav anchor to #rooms did not scroll enough: scrollY={y1}")

        # Booking widget
        page.locator("#booking").scroll_into_view_if_needed()
        page.locator("#checkin").fill("2026-08-05")
        page.locator("#checkout").fill("2026-08-08")
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(400)
        if not page.locator("#guestDropdown.open").count():
            errors.append("Guest panel did not open")
        page.locator("#adultsPlus").click()
        page.locator("#childrenPlus").click()
        page.wait_for_timeout(300)
        summary = page.locator("#guestSummary").inner_text()
        if "3 adults" not in summary or "1 child" not in summary:
            errors.append(f"Guest summary unexpected: {summary}")

        for sel in ["#rooms", "#amenities", "#gallery", "#location", "#trust", "#footer"]:
            page.locator(sel).scroll_into_view_if_needed()
            page.wait_for_timeout(250)

        page.screenshot(path=str(ARTIFACTS / "hotel-madona-desktop.png"), full_page=True)

        # Mobile
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.evaluate("window.scrollTo(0, 0)")
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        if not page.locator("#mobileNav.open").count():
            errors.append("Mobile nav did not open")
        page.locator("#navClose").click()
        page.wait_for_timeout(300)
        logo_box_m = page.locator(".logo").bounding_box()
        if not logo_box_m or logo_box_m["x"] < 24:
            errors.append(f"Mobile logo cramped: {logo_box_m}")
        page.screenshot(path=str(ARTIFACTS / "hotel-madona-mobile.png"), full_page=True)

        browser.close()

    if errors:
        print("VERIFICATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
