#!/usr/bin/env python3
"""Visual verification for the Rīteņi guesthouse prototype."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8771/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)


def main():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2000)

        # Image load check
        broken = page.evaluate(
            """() => Array.from(document.images)
                .filter(img => !img.complete || img.naturalWidth === 0)
                .map(img => img.src)"""
        )
        if broken:
            errors.append(f"Broken images: {broken}")
        else:
            print(f"OK: all {page.evaluate('() => document.images.length')} images loaded")

        # Header spacing from edges
        spacing = page.evaluate(
            """() => {
                const header = document.querySelector('.header-inner');
                const brand = document.querySelector('.brand');
                const cta = document.querySelector('.header-cta');
                const hr = header.getBoundingClientRect();
                const br = brand.getBoundingClientRect();
                const cr = cta.getBoundingClientRect();
                return {
                    leftPad: br.left - hr.left,
                    rightPad: hr.right - cr.right,
                    brandFromViewport: br.left,
                    ctaFromViewportRight: window.innerWidth - cr.right
                };
            }"""
        )
        print("Header spacing:", spacing)
        if spacing["brandFromViewport"] < 28 or spacing["ctaFromViewportRight"] < 28:
            errors.append(f"Header too close to edges: {spacing}")

        # Smooth scroll behavior
        scroll_behavior = page.evaluate(
            "() => getComputedStyle(document.documentElement).scrollBehavior"
        )
        print("scroll-behavior:", scroll_behavior)
        if scroll_behavior != "smooth":
            errors.append(f"Expected smooth scroll-behavior, got {scroll_behavior}")

        # Click nav anchors and confirm section reached
        for section in ["#rooms", "#amenities", "#gallery", "#location", "#trust", "#booking"]:
            page.locator(f'a[href="{section}"]').first.click()
            page.wait_for_timeout(900)
            in_view = page.evaluate(
                """(sel) => {
                    const el = document.querySelector(sel);
                    const r = el.getBoundingClientRect();
                    return r.top < window.innerHeight * 0.55 && r.bottom > 0;
                }""",
                section,
            )
            print(f"Nav {section} in view:", in_view)
            if not in_view:
                errors.append(f"Section {section} not in view after nav click")

        # Booking widget
        page.locator("#booking").scroll_into_view_if_needed()
        page.locator("#checkin").fill("2026-08-10")
        page.locator("#checkout").fill("2026-08-14")
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(300)
        page.locator("#adultsPlus").click()
        page.locator("#childrenPlus").click()
        summary = page.locator("#guestSummary").inner_text()
        print("Guest summary:", summary)
        if "3" not in summary:
            errors.append(f"Guest counter failed: {summary}")
        page.locator("#roomType").select_option("cottage")
        page.mouse.click(10, 10)

        # Screenshots
        page.screenshot(path=str(ARTIFACTS / "riiteni-desktop-hero.png"), full_page=False)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(400)
        page.screenshot(path=str(ARTIFACTS / "riiteni-desktop-top.png"), full_page=False)
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.evaluate("window.scrollTo(0, 0)")
        page.screenshot(path=str(ARTIFACTS / "riiteni-mobile-hero.png"), full_page=False)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        page.screenshot(path=str(ARTIFACTS / "riiteni-mobile-menu.png"), full_page=False)

        # Mobile header spacing
        page.locator("#navClose").click()
        spacing_m = page.evaluate(
            """() => {
                const brand = document.querySelector('.brand').getBoundingClientRect();
                const cta = document.querySelector('.header-cta').getBoundingClientRect();
                return { left: brand.left, right: window.innerWidth - cta.right };
            }"""
        )
        print("Mobile header spacing:", spacing_m)
        if spacing_m["left"] < 24 or spacing_m["right"] < 24:
            errors.append(f"Mobile header cramped: {spacing_m}")

        browser.close()

    if errors:
        print("FAILURES:")
        for e in errors:
            print(" -", e)
        raise SystemExit(1)
    print("All verification checks passed.")


if __name__ == "__main__":
    main()
