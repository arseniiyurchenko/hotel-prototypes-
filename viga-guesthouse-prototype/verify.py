#!/usr/bin/env python3
"""Verify VIGA guesthouse prototype: images, widget, nav, layout."""

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
        page.wait_for_timeout(2500)

        # Images
        imgs = page.locator("img").all()
        for i, img in enumerate(imgs):
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            src = img.get_attribute("src") or ""
            if not ok:
                errors.append(f"Broken image [{i}]: {src}")

        # Hero background should load (check computed background-image URL via network)
        hero_ok = page.evaluate(
            """() => {
              const el = document.querySelector('.hero-bg');
              if (!el) return false;
              const bg = getComputedStyle(el).backgroundImage;
              return bg.includes('20170111_145729.jpg');
            }"""
        )
        if not hero_ok:
            errors.append("Hero background image missing")

        # Header spacing from corners
        spacing = page.evaluate(
            """() => {
              const logo = document.querySelector('.logo');
              const cta = document.querySelector('.header-cta .btn-primary');
              const lr = logo.getBoundingClientRect();
              const cr = cta.getBoundingClientRect();
              return { left: lr.left, right: window.innerWidth - cr.right };
            }"""
        )
        if spacing["left"] < 24:
            errors.append(f"Logo too close to left edge: {spacing['left']}px")
        if spacing["right"] < 24:
            errors.append(f"CTA too close to right edge: {spacing['right']}px")

        # Smooth scroll-behavior
        sb = page.evaluate("() => getComputedStyle(document.documentElement).scrollBehavior")
        if sb != "smooth":
            errors.append(f"html scroll-behavior is '{sb}', expected 'smooth'")

        # Booking widget
        page.locator("#checkin").fill("2026-07-20")
        page.locator("#checkout").fill("2026-07-24")
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(400)
        if not page.locator("#guestPanel.open").count():
            errors.append("Guest panel did not open")
        page.locator("#adultsPlus").click()
        page.locator("#childrenPlus").click()
        page.wait_for_timeout(300)
        summary = page.locator("#guestSummary").inner_text()
        if "3 adults" not in summary or "1 child" not in summary:
            errors.append(f"Guest summary unexpected: {summary}")
        page.mouse.click(10, 200)
        page.wait_for_timeout(200)

        # Anchor nav — click and confirm scroll moved toward section
        for sel in ["#rooms", "#amenities", "#gallery", "#location", "#trust", "#booking"]:
            before = page.evaluate("() => window.scrollY")
            page.locator(f'a[href="{sel}"]').first.click()
            page.wait_for_timeout(900)
            after = page.evaluate("() => window.scrollY")
            top = page.evaluate(f"() => document.querySelector('{sel}').getBoundingClientRect().top")
            if abs(top) > 160 and after == before:
                errors.append(f"Nav to {sel} did not scroll (before={before}, after={after}, top={top})")

        # Sections exist
        for sel in ["#hero", "#booking", "#rooms", "#amenities", "#gallery", "#location", "#trust", "#footer"]:
            if not page.locator(sel).count():
                errors.append(f"Missing section {sel}")

        page.screenshot(path=str(ARTIFACTS / "viga-desktop.png"), full_page=True)

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
        page.screenshot(path=str(ARTIFACTS / "viga-mobile.png"), full_page=True)

        browser.close()

    if errors:
        print("VERIFICATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
