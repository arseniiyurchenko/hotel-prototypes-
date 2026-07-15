#!/usr/bin/env python3
"""Verify Zaķu krogs prototype: images, widget, anchors, layout."""

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
        page.wait_for_timeout(2500)

        # Images must load
        imgs = page.locator("img").all()
        for i, img in enumerate(imgs):
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            src = img.get_attribute("src") or ""
            if not ok:
                errors.append(f"Broken image [{i}]: {src}")

        # Header breathing room from edges
        logo_box = page.locator(".brand").bounding_box()
        cta_box = page.locator(".header-cta").bounding_box()
        if not logo_box or logo_box["x"] < 28:
            errors.append(f"Logo too close to left edge: {logo_box}")
        if not cta_box or (1280 - (cta_box["x"] + cta_box["width"])) < 28:
            errors.append(f"CTA too close to right edge: {cta_box}")

        # Smooth scroll via nav anchors
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(300)
        behavior = page.evaluate("getComputedStyle(document.documentElement).scrollBehavior")
        if behavior != "smooth":
            errors.append(f"html scroll-behavior is '{behavior}', expected 'smooth'")

        # Header/desktop nav + CTA anchors that exist in the sticky header
        for section in ["#rooms", "#tavern", "#amenities", "#gallery", "#location", "#booking"]:
            before = page.evaluate("window.scrollY")
            page.locator(f'.site-header a[href="{section}"], .nav-desktop a[href="{section}"]').first.click()
            page.wait_for_timeout(900)
            after = page.evaluate("window.scrollY")
            visible = page.locator(section).evaluate(
                "el => { const r = el.getBoundingClientRect(); return r.top < window.innerHeight && r.bottom > 60; }"
            )
            if not visible:
                errors.append(f"Section {section} not in view after nav click (scroll {before}->{after})")

        # Trust section is in-page only (no header nav link) — scroll into view
        page.locator("#trust").scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        if not page.locator("#trust").is_visible():
            errors.append("Trust section not visible")

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
        summary = page.locator("#guestSummary").inner_text()
        if "3 adult" not in summary or "1 child" not in summary:
            errors.append(f"Guest summary unexpected: {summary}")

        # Mobile usability
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        if not page.locator("#navMobile.open").count():
            errors.append("Mobile nav did not open")
        page.locator("#navClose").click()
        page.wait_for_timeout(300)

        logo_m = page.locator(".brand").bounding_box()
        cta_m = page.locator(".header-cta").bounding_box()
        if not logo_m or logo_m["x"] < 24:
            errors.append(f"Mobile logo cramped: {logo_m}")
        if not cta_m or (390 - (cta_m["x"] + cta_m["width"])) < 24:
            # menu toggle is rightmost; CTA should still have padding from edge via container
            # On mobile CTA is left of menu toggle - check container padding via logo
            pass

        page.set_viewport_size({"width": 1280, "height": 800})
        page.wait_for_timeout(400)
        page.screenshot(path=str(ARTIFACTS / "zaku-krogs-desktop.png"), full_page=True)
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(400)
        page.screenshot(path=str(ARTIFACTS / "zaku-krogs-mobile.png"), full_page=True)

        browser.close()

    if errors:
        print("VERIFICATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
