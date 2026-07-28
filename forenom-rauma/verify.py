#!/usr/bin/env python3
"""Verify Forenom Rauma prototype: images, widget, layout."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/forenom-rauma/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)


def main():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(3500)  # allow CDN fail → local fallback

        imgs = page.locator("img").all()
        for i, img in enumerate(imgs):
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            src = img.get_attribute("src") or ""
            if not ok:
                errors.append(f"Broken image [{i}]: {src}")

        # Hero uses remote + local layered backgrounds; local mirror must resolve
        hero_ok = page.evaluate(
            """() => new Promise(resolve => {
              const im = new Image();
              im.onload = () => resolve(im.naturalWidth > 0);
              im.onerror = () => resolve(false);
              im.src = 'images/rauma-living.png';
            })"""
        )
        if not hero_ok:
            errors.append("Hero background image failed to load")

        page.locator("#checkin").fill("2026-08-05")
        page.locator("#checkout").fill("2026-08-08")
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

        for sel in ["#rooms", "#amenities", "#gallery", "#location", "#trust"]:
            page.locator(sel).scroll_into_view_if_needed()
            page.wait_for_timeout(300)

        page.screenshot(path=str(ARTIFACTS / "forenom-rauma-desktop.png"), full_page=True)

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        if not page.locator("#navMobile.open").count():
            errors.append("Mobile nav did not open")
        page.locator("#navClose").click()
        page.screenshot(path=str(ARTIFACTS / "forenom-rauma-mobile.png"), full_page=True)

        browser.close()

    if errors:
        print("VERIFICATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
