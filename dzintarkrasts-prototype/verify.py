#!/usr/bin/env python3
"""Verify dzintarkrasts-prototype/index.html."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
URL = (ROOT / "index.html").as_uri()
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)


def main():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(URL, wait_until="networkidle", timeout=120000)
        page.wait_for_timeout(2000)

        imgs = page.evaluate(
            """() => Array.from(document.images).map(img => ({
                src: img.currentSrc || img.src,
                ok: img.complete && img.naturalWidth > 0,
                w: img.naturalWidth
            }))"""
        )
        for i, img in enumerate(imgs):
            status = "OK" if img["ok"] else "BROKEN"
            print(f"  [{status}] {img['src'][:100]}")
            if not img["ok"]:
                errors.append(f"Broken image [{i}]: {img['src']}")

        # Header spacing from corners
        spacing = page.evaluate(
            """() => {
              const header = document.querySelector('.site-header');
              const brand = document.querySelector('.brand');
              const cta = document.querySelector('.header-actions .btn-primary');
              const hb = header.getBoundingClientRect();
              const bb = brand.getBoundingClientRect();
              const cb = cta.getBoundingClientRect();
              return {
                leftGap: bb.left - hb.left,
                rightGap: hb.right - cb.right,
                brandLeft: bb.left,
                ctaRightFromEdge: window.innerWidth - cb.right
              };
            }"""
        )
        print(f"Header spacing: {spacing}")
        if spacing["brandLeft"] < 24 or spacing["ctaRightFromEdge"] < 24:
            errors.append(f"Header cramped against corners: {spacing}")

        # Smooth scroll via nav anchors
        behavior = page.evaluate("() => getComputedStyle(document.documentElement).scrollBehavior")
        print(f"scroll-behavior: {behavior}")
        if behavior != "smooth":
            errors.append(f"Expected smooth scroll-behavior, got {behavior}")

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(400)
        page.locator('.nav-desktop a[href="#rooms"]').click()
        page.wait_for_timeout(1200)
        y_after = page.evaluate("() => window.scrollY")
        print(f"After #rooms nav click scrollY={y_after}")
        if y_after < 200:
            errors.append("Nav anchor did not scroll to rooms")

        # Booking widget
        page.locator("#booking").scroll_into_view_if_needed()
        page.locator("#checkin").fill("2026-08-10")
        page.locator("#checkout").fill("2026-08-14")
        page.locator("#guestsDisplay").click()
        page.wait_for_timeout(300)
        if not page.locator("#guestPanel.open").count():
            errors.append("Guest panel did not open")
        page.locator('[data-target="adults"][data-action="increase"]').click()
        page.locator('[data-target="children"][data-action="increase"]').click()
        label = page.locator("#guestsLabel").inner_text()
        print(f"Guests label: {label}")
        if "3 adult" not in label or "1 child" not in label:
            errors.append(f"Guest stepper failed: {label}")

        page.locator("#bookingForm button[type=submit]").click()
        page.wait_for_timeout(300)
        if not page.locator("#bookingFeedback.show").count():
            errors.append("Booking feedback not shown")

        # Mobile
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(400)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(200)
        mobile_spacing = page.evaluate(
            """() => {
              const brand = document.querySelector('.brand').getBoundingClientRect();
              const cta = document.querySelector('.header-actions .btn-primary').getBoundingClientRect();
              const overflowX = document.documentElement.scrollWidth > window.innerWidth + 1;
              return {
                brandLeft: brand.left,
                ctaRight: window.innerWidth - cta.right,
                overflowX,
                scrollWidth: document.documentElement.scrollWidth,
                innerWidth: window.innerWidth
              };
            }"""
        )
        print(f"Mobile header spacing: {mobile_spacing}")
        if mobile_spacing["brandLeft"] < 20 or mobile_spacing["ctaRight"] < 20 or mobile_spacing["overflowX"]:
            errors.append(f"Mobile header cramped: {mobile_spacing}")

        page.locator("#menuToggle").click()
        page.wait_for_selector("#navMobile.open")

        page.screenshot(path=str(ARTIFACTS / "dzintarkrasts-desktop-full.png"), full_page=True)
        page.evaluate("window.scrollTo(0, 0)")
        page.screenshot(path=str(ARTIFACTS / "dzintarkrasts-mobile-hero.png"))

        browser.close()

    if errors:
        print("VERIFICATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
