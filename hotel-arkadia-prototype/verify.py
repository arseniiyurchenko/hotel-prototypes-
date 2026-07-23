#!/usr/bin/env python3
"""Verify Hotel Arkadia prototype: images, widget, anchors, layout."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/hotel-arkadia-prototype/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)


def main():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(URL, wait_until="networkidle", timeout=90000)
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

        # Smooth scroll via nav
        scroll_behavior = page.evaluate("() => getComputedStyle(document.documentElement).scrollBehavior")
        if scroll_behavior != "smooth":
            errors.append(f"html scroll-behavior is '{scroll_behavior}', expected 'smooth'")

        before = page.evaluate("() => window.scrollY")
        page.locator('.nav-desktop a[href="#rooms"]').click()
        page.wait_for_timeout(900)
        after = page.evaluate("() => window.scrollY")
        if after <= before + 50:
            errors.append("Nav click to #rooms did not scroll the page")

        # Booking widget
        tomorrow = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+3); return d.toISOString().split('T')[0]; }"
        )
        checkout = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+5); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#checkin").fill(tomorrow)
        page.locator("#checkout").fill(checkout)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(300)
        if not page.locator("#guestPanel.open").count():
            errors.append("Guest panel did not open")
        page.locator("#adultsPlus").click()
        page.locator("#childrenPlus").click()
        page.wait_for_timeout(200)
        label = page.locator("#guestLabel").inner_text()
        if "3 adults" not in label or "1 child" not in label:
            errors.append(f"Guest label unexpected: {label}")
        page.locator("#roomPref").select_option("suite")
        page.mouse.click(200, 200)

        for sel in ["#amenities", "#gallery", "#location", "#trust", "#footer"]:
            page.locator(sel).scroll_into_view_if_needed()
            page.wait_for_timeout(250)

        # Mobile
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(400)
        page.evaluate("window.scrollTo(0, 0)")
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        if not page.locator("#navMobile.open").count():
            errors.append("Mobile nav did not open")
        page.locator("#navClose").click()
        page.wait_for_timeout(300)

        page.screenshot(path=str(ARTIFACTS / "hotel-arkadia-desktop.png"), full_page=False)
        page.set_viewport_size({"width": 1280, "height": 800})
        page.wait_for_timeout(300)
        page.screenshot(path=str(ARTIFACTS / "hotel-arkadia-full.png"), full_page=True)

        browser.close()

    if errors:
        print("VERIFICATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
