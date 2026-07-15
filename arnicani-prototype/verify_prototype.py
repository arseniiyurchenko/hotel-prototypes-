#!/usr/bin/env python3
"""Verify Arnicāni prototype: images, widget, smooth scroll, layout."""

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
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(2000)

        # Images
        imgs = page.locator("img").all()
        print(f"Found {len(imgs)} img elements")
        for i, img in enumerate(imgs):
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            src = img.get_attribute("src") or ""
            if not ok:
                errors.append(f"Broken image [{i}]: {src}")
            else:
                w = img.evaluate("el => el.naturalWidth")
                print(f"  OK [{i}] {w}px — {src.split('/')[-1]}")

        # Hero background (CSS) — check URL loads
        hero_ok = page.evaluate("""() => {
          const el = document.querySelector('.hero-bg');
          const bg = getComputedStyle(el).backgroundImage;
          return bg && bg.includes('IMG_5832');
        }""")
        if not hero_ok:
            errors.append("Hero background image CSS missing")

        # Header spacing from edges
        spacing = page.evaluate("""() => {
          const logo = document.querySelector('.logo');
          const cta = document.querySelector('.header-cta');
          const lr = logo.getBoundingClientRect();
          const cr = cta.getBoundingClientRect();
          return { logoLeft: lr.left, ctaRight: window.innerWidth - cr.right };
        }""")
        print(f"Header spacing: logoLeft={spacing['logoLeft']:.1f} ctaRight={spacing['ctaRight']:.1f}")
        if spacing["logoLeft"] < 24:
            errors.append(f"Logo too close to left edge: {spacing['logoLeft']}")
        if spacing["ctaRight"] < 24:
            errors.append(f"CTA too close to right edge: {spacing['ctaRight']}")

        # Smooth scroll via nav
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(300)
        behavior = page.evaluate("() => getComputedStyle(document.documentElement).scrollBehavior")
        print(f"scroll-behavior: {behavior}")
        if behavior != "smooth":
            errors.append(f"html scroll-behavior is '{behavior}', expected smooth")

        page.locator('a.nav-desktop a[href="#amenities"], .nav-desktop a[href="#amenities"]').first.click()
        page.wait_for_timeout(900)
        y1 = page.evaluate("() => window.scrollY")
        print(f"After amenities nav click, scrollY={y1}")
        if y1 < 100:
            errors.append("Nav click did not scroll to amenities")

        # Booking widget
        page.locator("#booking").scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        page.locator("#checkin").fill("2026-07-20")
        page.locator("#checkout").fill("2026-07-24")
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(400)
        if not page.locator("#guestPanel.open").count():
            errors.append("Guest panel did not open")
        page.locator("#adultsPlus").click()
        page.locator("#childrenPlus").click()
        summary = page.locator("#guestSummary").inner_text()
        print(f"Guest summary: {summary}")
        if "3 adults" not in summary or "1 child" not in summary:
            errors.append(f"Guest summary unexpected: {summary}")

        # Sections present
        for sel in ["#hero", "#booking", "#rooms", "#amenities", "#gallery", "#location", "#trust", "#footer"]:
            if not page.locator(sel).count():
                errors.append(f"Missing section {sel}")

        page.screenshot(path=str(ARTIFACTS / "arnicani-desktop.png"), full_page=True)

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

        mobile_spacing = page.evaluate("""() => {
          const logo = document.querySelector('.logo');
          const toggle = document.querySelector('.menu-toggle');
          const lr = logo.getBoundingClientRect();
          const tr = toggle.getBoundingClientRect();
          return { logoLeft: lr.left, toggleRight: window.innerWidth - tr.right };
        }""")
        print(f"Mobile spacing: logoLeft={mobile_spacing['logoLeft']:.1f} toggleRight={mobile_spacing['toggleRight']:.1f}")
        if mobile_spacing["logoLeft"] < 20:
            errors.append(f"Mobile logo cramped: {mobile_spacing['logoLeft']}")

        page.screenshot(path=str(ARTIFACTS / "arnicani-mobile.png"), full_page=True)

        browser.close()

    if errors:
        print("VERIFICATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
