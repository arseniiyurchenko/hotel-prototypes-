#!/usr/bin/env python3
"""Verify Hotel Ērgļi prototype: images, widget, smooth scroll, layout."""

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
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2000)

        # Images
        imgs = page.locator("img").all()
        for i, img in enumerate(imgs):
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            src = img.get_attribute("src") or ""
            if not ok:
                errors.append(f"Broken image [{i}]: {src}")

        # Header spacing — logo and CTA not jammed to edges
        logo_box = page.locator(".logo").bounding_box()
        cta_box = page.locator(".header-cta").bounding_box()
        if not logo_box or logo_box["x"] < 24:
            errors.append(f"Logo too close to left edge: {logo_box}")
        if not cta_box or (1280 - (cta_box["x"] + cta_box["width"])) < 24:
            errors.append(f"CTA too close to right edge: {cta_box}")

        # Smooth scroll via nav
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(300)
        behavior = page.evaluate("() => getComputedStyle(document.documentElement).scrollBehavior")
        if behavior != "smooth":
            errors.append(f"scroll-behavior is '{behavior}', expected 'smooth'")

        page.locator('.nav-desktop a[href="#rooms"]').click()
        page.wait_for_timeout(900)
        rooms_top = page.evaluate("() => document.getElementById('rooms').getBoundingClientRect().top")
        if abs(rooms_top) > 120:
            # sticky header offset is fine; ensure we landed near rooms
            if rooms_top > 400 or rooms_top < -50:
                errors.append(f"Rooms section not near viewport after nav click: top={rooms_top}")

        # Booking widget
        page.locator("#booking").scroll_into_view_if_needed()
        page.locator("#checkin").fill("2026-08-05")
        page.locator("#checkout").fill("2026-08-08")
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(400)
        if not page.locator("#guestPanel.open").count():
            errors.append("Guest panel did not open")
        page.locator("#adultsPlus").click()
        page.locator("#childrenPlus").click()
        page.locator("#roomType").select_option("suite")
        page.wait_for_timeout(300)

        for sel in ["#amenities", "#gallery", "#location", "#trust", "#footer"]:
            page.locator(sel).scroll_into_view_if_needed()
            page.wait_for_timeout(250)

        # Mobile
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        if not page.locator("#navMobile.open").count():
            errors.append("Mobile nav did not open")
        page.locator("#navClose").click()
        page.wait_for_timeout(300)

        page.set_viewport_size({"width": 1280, "height": 800})
        page.wait_for_timeout(400)
        page.screenshot(path=str(ARTIFACTS / "hotel-ergli-desktop.png"), full_page=True)

        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(1000)
        page.screenshot(path=str(ARTIFACTS / "hotel-ergli-mobile.png"), full_page=True)

        browser.close()

    if errors:
        print("VERIFICATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
