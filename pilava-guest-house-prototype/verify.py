#!/usr/bin/env python3
"""Verify Pilava prototype: images, anchors, widget, layout."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)

SECTIONS = [
    "#hero",
    "#booking",
    "#accommodation",
    "#amenities",
    "#gallery",
    "#location",
    "#trust",
    "#footer",
]


def main():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(URL, wait_until="networkidle", timeout=120000)
        page.wait_for_timeout(2000)

        imgs = page.locator("img").all()
        if not imgs:
            errors.append("No images found")
        for i, img in enumerate(imgs):
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            src = img.get_attribute("src") or ""
            if not ok:
                errors.append(f"Broken image [{i}]: {src}")

        for sel in SECTIONS:
            if page.locator(sel).count() == 0:
                errors.append(f"Missing section: {sel}")

        # Header spacing from corners
        spacing = page.evaluate(
            """() => {
              const header = document.querySelector('.header-inner');
              const logo = document.querySelector('.logo');
              const cta = document.querySelector('.header-cta');
              const hr = header.getBoundingClientRect();
              const lr = logo.getBoundingClientRect();
              const cr = cta.getBoundingClientRect();
              return {
                leftGap: lr.left - hr.left,
                rightGap: hr.right - cr.right,
                logoLeft: lr.left,
                ctaRightFromEdge: window.innerWidth - cr.right,
              };
            }"""
        )
        if spacing["logoLeft"] < 24:
            errors.append(f"Logo too close to left edge: {spacing['logoLeft']}px")
        if spacing["ctaRightFromEdge"] < 24:
            errors.append(f"CTA too close to right edge: {spacing['ctaRightFromEdge']}px")

        # Smooth scroll behavior present
        behavior = page.evaluate("() => getComputedStyle(document.documentElement).scrollBehavior")
        if behavior != "smooth":
            errors.append(f"html scroll-behavior is '{behavior}', expected 'smooth'")

        # Booking widget
        page.locator("#checkin").fill("2026-07-28")
        page.locator("#checkout").fill("2026-07-31")
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(400)
        if not page.locator("#guestPanel.open").count():
            errors.append("Guest panel did not open")
        page.locator("#adultsPlus").click()
        page.locator("#childrenPlus").click()
        summary = page.locator("#guestSummary").inner_text()
        if "3 guests" not in summary and "3" not in summary:
            errors.append(f"Guest summary unexpected: {summary}")

        # Anchor click scrolls
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(300)
        page.locator('.nav-desktop a[href="#gallery"]').click()
        page.wait_for_timeout(900)
        y = page.evaluate("() => window.scrollY")
        if y < 100:
            errors.append("Nav anchor click did not scroll to gallery")

        page.screenshot(path=str(ARTIFACTS / "pilava-desktop.png"), full_page=True)

        # Mobile
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        if not page.locator("#navMobile.open").count():
            errors.append("Mobile nav did not open")
        page.locator("#navClose").click()
        page.wait_for_timeout(300)
        page.screenshot(path=str(ARTIFACTS / "pilava-mobile.png"), full_page=True)

        # Mobile header spacing (CTA hidden; logo + menu toggle)
        mspace = page.evaluate(
            """() => {
              const logo = document.querySelector('.logo').getBoundingClientRect();
              const toggle = document.querySelector('#menuToggle').getBoundingClientRect();
              return { logoLeft: logo.left, toggleRight: window.innerWidth - toggle.right };
            }"""
        )
        if mspace["logoLeft"] < 24:
            errors.append(f"Mobile logo cramped: {mspace['logoLeft']}px")
        if mspace["toggleRight"] < 24:
            errors.append(f"Mobile toggle cramped: {mspace['toggleRight']}px")

        browser.close()

    if errors:
        print("VERIFICATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print("All checks passed.")
    print(f"Desktop header spacing: {spacing}")
    print(f"Mobile header spacing: {mspace}")


if __name__ == "__main__":
    main()
