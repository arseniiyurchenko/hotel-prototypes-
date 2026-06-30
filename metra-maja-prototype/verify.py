#!/usr/bin/env python3
"""Verify Mētras Māja prototype: images, booking widget, layout."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8766/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)


def main():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(URL, wait_until="networkidle")

        broken = page.evaluate("""
            () => {
                const imgs = [...document.querySelectorAll('img')];
                return imgs.filter(img => !img.complete || img.naturalWidth === 0)
                    .map(img => img.src);
            }
        """)
        if broken:
            errors.append(f"Broken images: {broken}")

        page.locator("#checkin").fill("2026-07-10")
        page.locator("#checkout").fill("2026-07-14")
        page.locator("#guestTrigger").click()
        page.locator("#adultsPlus").click()
        page.locator("#roomType").select_option("two-room")
        if not page.locator("#guestDropdown.open").is_visible():
            errors.append("Guest dropdown did not open")

        for sel in ["#rooms", "#amenities", "#gallery", "#location", "#trust"]:
            page.locator(sel).scroll_into_view_if_needed()
            box = page.locator(sel).bounding_box()
            if not box or box["height"] < 50:
                errors.append(f"Section {sel} appears empty or collapsed")

        page.screenshot(path=str(ARTIFACTS / "metra-maja-desktop.png"), full_page=True)

        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(URL, wait_until="networkidle")
        page.locator("#menuToggle").click()
        if not page.locator("#mobileNav.open").is_visible():
            errors.append("Mobile nav did not open")
        page.screenshot(path=str(ARTIFACTS / "metra-maja-mobile.png"), full_page=True)

        browser.close()

    if errors:
        print("VERIFICATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)

    print("VERIFICATION PASSED")


if __name__ == "__main__":
    main()
