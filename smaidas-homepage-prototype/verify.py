#!/usr/bin/env python3
"""Verify Smaidas homepage prototype."""

from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
URL = "http://127.0.0.1:8765/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)


def main():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(URL, wait_until="networkidle", timeout=120000)
        page.wait_for_timeout(2000)

        # Images
        imgs = page.locator("img").all()
        for i, img in enumerate(imgs):
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            src = img.get_attribute("src") or ""
            if not ok:
                errors.append(f"Broken image [{i}]: {src}")

        # Header spacing from edges
        logo_box = page.locator(".logo").bounding_box()
        cta_box = page.locator(".header-cta").bounding_box()
        if not logo_box or logo_box["x"] < 28:
            errors.append(f"Logo too close to left edge: {logo_box}")
        if not cta_box or (1280 - (cta_box["x"] + cta_box["width"])) < 28:
            errors.append(f"CTA too close to right edge: {cta_box}")

        # Smooth scroll via anchor
        behavior = page.evaluate("() => getComputedStyle(document.documentElement).scrollBehavior")
        if behavior != "smooth":
            errors.append(f"html scroll-behavior is '{behavior}', expected 'smooth'")

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(300)
        page.locator('a.header-cta').click()
        page.wait_for_timeout(900)
        y_after_cta = page.evaluate("() => window.scrollY")
        if y_after_cta < 100:
            errors.append("CTA did not scroll to booking section")

        for sel in ["#accommodation", "#amenities", "#gallery", "#location", "#trust", "#footer"]:
            page.locator(f'a[href="{sel}"]').first.click()
            page.wait_for_timeout(800)
            top = page.evaluate(
                f"() => document.querySelector('{sel}').getBoundingClientRect().top"
            )
            # Should land near sticky header, not far down the page
            if top > 200 or top < -80:
                errors.append(f"Anchor {sel} landed poorly (top={top})")

        # Booking widget
        page.locator("#checkin").fill("2026-07-20")
        page.locator("#checkout").fill("2026-07-23")
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(400)
        if not page.locator("#guestPanel.open").count():
            errors.append("Guest panel did not open")
        page.locator("#adultsPlus").click()
        page.locator("#childrenPlus").click()
        page.wait_for_timeout(200)
        label = page.locator("#guestTrigger").inner_text()
        if "3 adults" not in label or "1 child" not in label:
            errors.append(f"Guest label unexpected: {label}")
        page.locator("#bookingForm button[type=submit]").click()
        page.wait_for_timeout(300)
        if not page.locator("#bookingFeedback.show").count():
            errors.append("Booking feedback did not show")

        page.screenshot(path=str(ARTIFACTS / "smaidas-desktop.png"), full_page=True)

        # Mobile
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.evaluate("window.scrollTo(0, 0)")
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        if not page.locator("#navMobile.open").count():
            errors.append("Mobile nav did not open")
        page.locator("#navClose").click()
        page.wait_for_timeout(300)
        page.screenshot(path=str(ARTIFACTS / "smaidas-mobile.png"), full_page=True)

        browser.close()

    if errors:
        print("VERIFICATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
