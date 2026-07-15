#!/usr/bin/env python3
"""Verify Smeceres Krogs prototype: images, widget, layout, smooth scroll."""

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
        page.wait_for_timeout(2500)

        # Images
        imgs = page.locator("img").all()
        for i, img in enumerate(imgs):
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            src = img.get_attribute("src") or ""
            if not ok:
                errors.append(f"Broken image [{i}]: {src}")

        # Header spacing from edges
        logo_box = page.locator(".logo").bounding_box()
        cta_box = page.locator(".btn-header").bounding_box()
        if not logo_box or logo_box["x"] < 24:
            errors.append(f"Logo too close to left edge: {logo_box}")
        if not cta_box or (1280 - (cta_box["x"] + cta_box["width"])) < 24:
            errors.append(f"CTA too close to right edge: {cta_box}")

        # Booking widget
        page.locator("#checkin").fill("2026-07-20")
        page.locator("#checkout").fill("2026-07-23")
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(400)
        if not page.locator("#guestPanel.open").count():
            errors.append("Guest panel did not open")
        page.locator("#adultsPlus").click()
        page.locator("#childrenPlus").click()
        page.locator("#roomType").select_option("triple")
        page.wait_for_timeout(300)

        # Smooth scroll via nav anchors
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(400)
        behavior = page.evaluate("getComputedStyle(document.documentElement).scrollBehavior")
        if behavior != "smooth":
            errors.append(f"scroll-behavior is '{behavior}', expected 'smooth'")

        for sel in ["#rooms", "#restaurant", "#amenities", "#gallery", "#location", "#trust"]:
            before = page.evaluate("window.scrollY")
            page.locator(f'a[href="{sel}"]').first.click()
            page.wait_for_timeout(900)
            after = page.evaluate("window.scrollY")
            if after <= before and sel != "#hero":
                # rooms is below booking; should move
                if abs(after - before) < 50:
                    errors.append(f"Nav to {sel} did not scroll meaningfully ({before} -> {after})")

        # Required section anchors exist
        for sid in ["hero", "booking", "rooms", "restaurant", "amenities", "gallery", "location", "trust", "footer"]:
            if not page.locator(f"#{sid}").count():
                errors.append(f"Missing section id=#{sid}")

        page.screenshot(path=str(ARTIFACTS / "smeceres-krogs-desktop.png"), full_page=True)

        # Mobile
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        if not page.locator("#navMobile.open").count():
            errors.append("Mobile nav did not open")
        page.locator("#navClose").click()
        page.screenshot(path=str(ARTIFACTS / "smeceres-krogs-mobile.png"), full_page=True)

        browser.close()

    if errors:
        print("VERIFICATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
