#!/usr/bin/env python3
"""Verify Villa Santa prototype: images, widget, layout."""

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
        page.wait_for_timeout(1500)

        imgs = page.locator("img").all()
        for i, img in enumerate(imgs):
            ok = img.evaluate(
                "el => el.complete && el.naturalWidth > 0"
            )
            src = img.get_attribute("src") or ""
            if not ok:
                errors.append(f"Broken image [{i}]: {src}")

        page.locator("#checkin").fill("2026-07-05")
        page.locator("#checkout").fill("2026-07-08")
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(400)
        if not page.locator("#guestPanel.open").count():
            errors.append("Guest panel did not open")
        page.locator("#adultsPlus").click()
        page.locator("#childrenPlus").click()
        page.locator("#roomType").select_option("suite")
        page.wait_for_timeout(300)

        for sel in ["#rooms", "#amenities", "#gallery", "#location", "#trust"]:
            page.locator(sel).scroll_into_view_if_needed()
            page.wait_for_timeout(300)

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        if not page.locator("#navMobile.open").count():
            errors.append("Mobile nav did not open")
        page.locator("#navClose").click()

        page.screenshot(path=str(ARTIFACTS / "villasanta-desktop.png"), full_page=True)

        browser.close()

    if errors:
        print("VERIFICATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
