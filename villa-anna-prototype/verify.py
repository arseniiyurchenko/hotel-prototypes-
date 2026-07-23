#!/usr/bin/env python3
"""Verify Villa Anna prototype: images, header spacing, smooth scroll, widget, mobile."""

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
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(2000)

        # Images
        imgs = page.locator("img").all()
        for i, img in enumerate(imgs):
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            src = img.get_attribute("src") or ""
            if not ok:
                errors.append(f"Broken image [{i}]: {src}")

        # Header spacing from corners
        spacing = page.evaluate(
            """() => {
              const header = document.querySelector('.site-header');
              const logo = document.querySelector('.logo');
              const cta = document.querySelector('.header-inner .btn-cta');
              const hr = header.getBoundingClientRect();
              const lr = logo.getBoundingClientRect();
              const cr = cta.getBoundingClientRect();
              return {
                logoLeft: lr.left - hr.left,
                ctaRight: hr.right - cr.right,
                padX: getComputedStyle(document.querySelector('.container')).paddingLeft
              };
            }"""
        )
        if spacing["logoLeft"] < 28:
            errors.append(f"Logo too close to left edge: {spacing['logoLeft']}px")
        if spacing["ctaRight"] < 28:
            errors.append(f"CTA too close to right edge: {spacing['ctaRight']}px")

        # Smooth scroll via nav anchor
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(300)
        scroll_behavior = page.evaluate(
            "() => getComputedStyle(document.documentElement).scrollBehavior"
        )
        if scroll_behavior != "smooth":
            errors.append(f"html scroll-behavior is '{scroll_behavior}', expected smooth")

        before = page.evaluate("() => window.scrollY")
        page.locator('.nav-desktop a[href="#rooms"]').click()
        page.wait_for_timeout(900)
        mid = page.evaluate("() => window.scrollY")
        page.wait_for_timeout(700)
        after = page.evaluate("() => window.scrollY")
        if after <= before + 50:
            errors.append("Nav link to #rooms did not scroll the page")
        # During smooth scroll, mid may be between before and after; accept either mid != after or after far
        rooms_top = page.evaluate(
            "() => document.getElementById('rooms').getBoundingClientRect().top"
        )
        if abs(rooms_top) > 160:
            errors.append(f"#rooms not near viewport after nav click (top={rooms_top})")

        # Booking widget
        page.locator("#booking").scroll_into_view_if_needed()
        page.locator("#checkin").fill("2026-08-05")
        page.locator("#checkout").fill("2026-08-08")
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(400)
        if not page.locator("#guestPanel.open").count():
            errors.append("Guest panel did not open")
        page.locator("#adultsPlus").click()
        page.locator("#childrenPlus").click()
        page.locator("#roomType").select_option("sea-view")
        page.wait_for_timeout(300)

        for sel in ["#amenities", "#gallery", "#location", "#trust", "#contact"]:
            page.locator(sel).scroll_into_view_if_needed()
            page.wait_for_timeout(250)

        page.screenshot(path=str(ARTIFACTS / "villa-anna-desktop.png"), full_page=True)

        # Mobile
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        mobile_spacing = page.evaluate(
            """() => {
              const header = document.querySelector('.site-header');
              const logo = document.querySelector('.logo');
              const cta = document.querySelector('.header-inner .btn-cta');
              const hr = header.getBoundingClientRect();
              const lr = logo.getBoundingClientRect();
              const cr = cta.getBoundingClientRect();
              return { logoLeft: lr.left - hr.left, ctaRight: hr.right - cr.right };
            }"""
        )
        if mobile_spacing["logoLeft"] < 28:
            errors.append(f"Mobile logo too close to edge: {mobile_spacing['logoLeft']}px")
        if mobile_spacing["ctaRight"] < 28:
            errors.append(f"Mobile CTA too close to edge: {mobile_spacing['ctaRight']}px")

        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        if not page.locator("#navMobile.open").count():
            errors.append("Mobile nav did not open")
        page.locator("#navClose").click()
        page.wait_for_timeout(300)
        page.screenshot(path=str(ARTIFACTS / "villa-anna-mobile.png"), full_page=True)

        browser.close()

    if errors:
        print("VERIFICATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print("All checks passed.")
    print(f"Desktop header spacing: logo {spacing['logoLeft']:.0f}px, CTA {spacing['ctaRight']:.0f}px")


if __name__ == "__main__":
    main()
