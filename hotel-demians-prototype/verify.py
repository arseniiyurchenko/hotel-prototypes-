#!/usr/bin/env python3
"""Verify Hotel Demians prototype: images, widget, smooth scroll, layout."""

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
                print(f"  OK [{i}] {w}px — {src[:90]}")

        # Hero background (CSS) — fetch URL
        hero_ok = page.evaluate("""() => {
          const el = document.querySelector('.hero-bg');
          const bg = getComputedStyle(el).backgroundImage;
          const m = bg.match(/url\\(["']?(.*?)["']?\\)/);
          return m ? m[1] : null;
        }""")
        print(f"Hero bg URL: {hero_ok}")

        # Header spacing from corners
        spacing = page.evaluate("""() => {
          const logo = document.querySelector('.logo');
          const cta = document.querySelector('.header-cta');
          const lr = logo.getBoundingClientRect();
          const cr = cta.getBoundingClientRect();
          return { logoLeft: lr.left, ctaRight: window.innerWidth - cr.right, vw: window.innerWidth };
        }""")
        print(f"Header spacing: logoLeft={spacing['logoLeft']:.1f} ctaRight={spacing['ctaRight']:.1f}")
        if spacing["logoLeft"] < 24:
            errors.append(f"Logo too close to left edge: {spacing['logoLeft']:.1f}px")
        if spacing["ctaRight"] < 24:
            errors.append(f"CTA too close to right edge: {spacing['ctaRight']:.1f}px")

        # Smooth scroll behavior
        scroll_behavior = page.evaluate("() => getComputedStyle(document.documentElement).scrollBehavior")
        print(f"html scroll-behavior: {scroll_behavior}")
        if scroll_behavior != "smooth":
            errors.append(f"scroll-behavior is '{scroll_behavior}', expected 'smooth'")

        # Anchor navigation timing
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(400)
        page.click('a.nav-desktop[href="#rooms"], .nav-desktop a[href="#rooms"]')
        # Wait mid-scroll — if smooth, we shouldn't be instantly at rooms
        page.wait_for_timeout(200)
        y_mid = page.evaluate("() => window.scrollY")
        page.wait_for_timeout(1200)
        y_end = page.evaluate("() => window.scrollY")
        rooms_top = page.evaluate("() => document.getElementById('rooms').offsetTop")
        print(f"Scroll mid={y_mid:.0f} end={y_end:.0f} rooms≈{rooms_top}")
        if y_end < 100:
            errors.append("Nav link to #rooms did not scroll")

        # Booking widget
        page.locator("#checkin").fill("2026-07-20")
        page.locator("#checkout").fill("2026-07-23")
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(400)
        if not page.locator("#guestPanel.open").count():
            errors.append("Guest panel did not open")
        page.locator("#adultsPlus").click()
        page.locator("#childrenPlus").click()
        page.locator("#roomType").select_option("double")
        summary = page.locator("#guestSummary").inner_text()
        print(f"Guest summary: {summary}")
        if "3 adult" not in summary:
            errors.append(f"Unexpected guest summary: {summary}")

        for sel in ["#amenities", "#gallery", "#location", "#trust", "#footer"]:
            page.locator(sel).scroll_into_view_if_needed()
            page.wait_for_timeout(250)

        # Mobile
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        mobile_spacing = page.evaluate("""() => {
          const logo = document.querySelector('.logo');
          const toggle = document.querySelector('#menuToggle');
          const lr = logo.getBoundingClientRect();
          const tr = toggle.getBoundingClientRect();
          return { logoLeft: lr.left, toggleRight: window.innerWidth - tr.right };
        }""")
        print(f"Mobile spacing: logoLeft={mobile_spacing['logoLeft']:.1f} toggleRight={mobile_spacing['toggleRight']:.1f}")
        if mobile_spacing["logoLeft"] < 20:
            errors.append(f"Mobile logo cramped: {mobile_spacing['logoLeft']:.1f}px")
        if mobile_spacing["toggleRight"] < 20:
            errors.append(f"Mobile menu toggle cramped/overflow: {mobile_spacing['toggleRight']:.1f}px")

        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        if not page.locator("#navMobile.open").count():
            errors.append("Mobile nav did not open")
        page.locator("#navClose").click()

        page.screenshot(path=str(ARTIFACTS / "demians-mobile.png"), full_page=False)

        # Desktop screenshots with all sections revealed
        page.set_viewport_size({"width": 1280, "height": 800})
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(2200)
        page.evaluate("() => document.querySelectorAll('.reveal').forEach(el => el.classList.add('visible'))")
        page.screenshot(path=str(ARTIFACTS / "demians-desktop.png"), full_page=False)
        page.screenshot(path=str(ARTIFACTS / "demians-fullpage.png"), full_page=True)

        browser.close()

    if errors:
        print("VERIFICATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
