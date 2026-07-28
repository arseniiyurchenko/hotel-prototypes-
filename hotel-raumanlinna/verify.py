#!/usr/bin/env python3
"""Verify Hotel Kalliohovi prototype: images, booking widget, layout."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8767/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)


def main():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(1500)

        # Force lazy images into view so they load before assertion
        page.evaluate(
            """
            async () => {
              const imgs = [...document.images];
              for (const img of imgs) {
                img.scrollIntoView({block: 'center'});
                await new Promise(r => setTimeout(r, 150));
              }
              await Promise.all(imgs.map(img =>
                img.complete ? Promise.resolve()
                  : new Promise(res => { img.onload = img.onerror = res; })
              ));
            }
            """
        )
        page.wait_for_timeout(1000)

        imgs = page.locator("img").all()
        for i, img in enumerate(imgs):
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            src = img.get_attribute("src") or ""
            if not ok:
                errors.append(f"Broken image [{i}]: {src}")

        page.locator("#booking").scroll_into_view_if_needed()
        page.locator("#checkin").fill("2026-08-05")
        page.locator("#checkout").fill("2026-08-08")
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
            page.wait_for_timeout(250)
            box = page.locator(sel).bounding_box()
            if not box or box["height"] < 80:
                errors.append(f"Section too small or missing: {sel}")

        page.screenshot(path=str(ARTIFACTS / "hotel-raumanlinna-desktop.png"), full_page=True)

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.evaluate("window.scrollTo(0, 0)")
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        if not page.locator("#navMobile.open").count():
            errors.append("Mobile nav did not open")
        page.locator("#navClose").click()
        page.wait_for_timeout(300)
        page.screenshot(path=str(ARTIFACTS / "hotel-raumanlinna-mobile.png"), full_page=True)

        browser.close()

    if errors:
        print("VERIFICATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print(f"All checks passed. Images checked: {len(imgs)}")


if __name__ == "__main__":
    main()
