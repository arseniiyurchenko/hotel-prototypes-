#!/usr/bin/env python3
"""Verify Krasta Māja guest-house prototype: images, booking, layout."""

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

        brand = page.locator(".hero-brand")
        if not brand.is_visible():
            errors.append("Hero brand not visible")
        brand_box = brand.bounding_box()
        if not brand_box or brand_box["height"] < 40:
            errors.append("Hero brand too small / not hero-level")

        page.locator("#checkin").fill("2026-07-20")
        page.locator("#checkout").fill("2026-07-24")
        page.locator("#guestTrigger").click()
        page.locator("#adultsPlus").click()
        page.locator("#stayType").select_option("weekend")
        if not page.locator("#guestDropdown.open").is_visible():
            errors.append("Guest dropdown did not open")

        page.locator("#bookingForm button[type='submit']").click()
        note = page.locator("#bookingNote").inner_text()
        if "prototips" not in note.lower() and "Pieejamība" not in note:
            errors.append(f"Booking submit did not update note: {note}")

        for sel in ["#intro", "#spaces", "#atmosphere", "#gallery", "#location", "#trust"]:
            page.locator(sel).scroll_into_view_if_needed()
            box = page.locator(sel).bounding_box()
            if not box or box["height"] < 50:
                errors.append(f"Section {sel} appears empty or collapsed")

        # Force lazy images into view, then wait for decode
        page.evaluate(
            """
            async () => {
              for (const img of document.querySelectorAll('img')) {
                img.scrollIntoView({ block: 'center' });
                await new Promise(r => setTimeout(r, 120));
              }
              await Promise.all([...document.images].map(img =>
                img.complete ? Promise.resolve() : new Promise(res => {
                  img.onload = img.onerror = res;
                })
              ));
            }
            """
        )
        page.wait_for_timeout(800)

        broken = page.evaluate(
            """
            () => {
                const imgs = [...document.querySelectorAll('img')];
                return imgs.filter(img => !img.complete || img.naturalWidth === 0)
                    .map(img => img.src);
            }
            """
        )
        if broken:
            errors.append(f"Broken images: {broken}")

        page.screenshot(path=str(ARTIFACTS / "krasta-maja-desktop.png"), full_page=True)

        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(URL, wait_until="networkidle")
        page.locator("#menuToggle").click()
        if not page.locator("#mobileNav.open").is_visible():
            errors.append("Mobile nav did not open")
        page.screenshot(path=str(ARTIFACTS / "krasta-maja-mobile.png"), full_page=True)

        browser.close()

    if errors:
        print("VERIFICATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)

    print("VERIFICATION PASSED")


if __name__ == "__main__":
    main()
