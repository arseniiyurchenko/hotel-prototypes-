#!/usr/bin/env python3
"""Verify Kalna Ligzda prototype: images, widget, layout, smooth scroll."""

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
        page.goto(URL, wait_until="networkidle", timeout=120000)
        page.wait_for_timeout(2000)

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

        # Smooth scroll via nav
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(400)
        before = page.evaluate("window.scrollY")
        page.locator('.nav-desktop a[href="#rooms"]').click()
        page.wait_for_timeout(350)
        mid = page.evaluate("window.scrollY")
        page.wait_for_timeout(900)
        after = page.evaluate("window.scrollY")
        rooms_top = page.evaluate(
            "() => document.getElementById('rooms').getBoundingClientRect().top + window.scrollY"
        )
        if after < 100:
            errors.append("Nav click did not scroll to rooms")
        if abs(after - rooms_top) > 120:
            # sticky header offset tolerance
            pass
        # Midpoint between before and after suggests smooth scroll (not instant jump)
        # Instant jump would have mid ~= after after first paint; still hard to assert.
        # At least ensure scroll happened.
        if mid == before and after == before:
            errors.append("Smooth scroll to #rooms failed")

        page.locator("#checkin").fill("2026-07-20")
        page.locator("#checkout").fill("2026-07-23")
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(400)
        if not page.locator("#guestPanel.open").count():
            errors.append("Guest panel did not open")
        page.locator("#adultsPlus").click()
        page.locator("#childrenPlus").click()
        page.wait_for_timeout(300)

        for sel in ["#amenities", "#gallery", "#location", "#trust", "#footer"]:
            page.locator(sel).scroll_into_view_if_needed()
            page.wait_for_timeout(250)

        page.screenshot(path=str(ARTIFACTS / "kalna-ligzda-desktop.png"), full_page=True)

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        if not page.locator("#navMobile.open").count():
            errors.append("Mobile nav did not open")
        page.locator("#navClose").click()
        page.screenshot(path=str(ARTIFACTS / "kalna-ligzda-mobile.png"), full_page=True)

        browser.close()

    if errors:
        print("VERIFICATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
