#!/usr/bin/env python3
"""Verify Saule guest house prototype: images, widget, anchors, layout."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8770/index.html"
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

        # Header breathing room
        logo_box = page.locator(".logo").bounding_box()
        cta_box = page.locator(".header-cta").bounding_box()
        if not logo_box or logo_box["x"] < 24:
            errors.append(f"Logo too close to left edge: {logo_box}")
        if not cta_box or (1280 - (cta_box["x"] + cta_box["width"])) < 24:
            errors.append(f"CTA too close to right edge: {cta_box}")

        # Smooth scroll behavior
        behavior = page.evaluate("() => getComputedStyle(document.documentElement).scrollBehavior")
        if behavior != "smooth":
            errors.append(f"html scroll-behavior is '{behavior}', expected 'smooth'")

        page.locator("#checkin").fill("2026-07-25")
        page.locator("#checkout").fill("2026-07-28")
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(400)
        if not page.locator("#guestDropdown.open").count():
            errors.append("Guest dropdown did not open")
        page.locator("#adultsPlus").click()
        page.locator("#childrenPlus").click()
        page.locator("#roomType").select_option("superior")
        page.wait_for_timeout(300)

        for sel in ["#rooms", "#amenities", "#gallery", "#location", "#trust", "#footer"]:
            if page.locator(sel).count() == 0:
                errors.append(f"Missing section {sel}")
            else:
                page.locator(sel).scroll_into_view_if_needed()
                page.wait_for_timeout(250)

        # Anchor nav click
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(300)
        page.locator('.nav-desktop a[href="#gallery"]').click()
        page.wait_for_timeout(900)

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(300)
        page.screenshot(path=str(ARTIFACTS / "saule-guesthouse-desktop.png"), full_page=False)
        page.screenshot(path=str(ARTIFACTS / "saule-guesthouse-full.png"), full_page=True)

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.evaluate("window.scrollTo(0, 0)")
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        if not page.locator("#mobileNav.open").count():
            errors.append("Mobile nav did not open")
        page.locator("#navClose").click()
        page.screenshot(path=str(ARTIFACTS / "saule-guesthouse-mobile.png"), full_page=False)

        browser.close()

    if errors:
        print("VERIFICATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
