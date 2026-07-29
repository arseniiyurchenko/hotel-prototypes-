#!/usr/bin/env python3
"""Verify Rauma Studios prototype: images, booking widget, layout."""

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
        page.wait_for_timeout(2000)

        imgs = page.locator("img").all()
        for i, img in enumerate(imgs):
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            src = img.get_attribute("src") or ""
            if not ok:
                errors.append(f"Broken image [{i}]: {src}")

        # Hero background is CSS — probe load via fetch
        hero_ok = page.evaluate(
            """async () => {
              const url = getComputedStyle(document.querySelector('.hero-bg')).backgroundImage;
              const m = url.match(/url\\(["']?(.*?)["']?\\)/);
              if (!m) return false;
              try {
                const r = await fetch(m[1], { method: 'HEAD', mode: 'cors' });
                return r.ok;
              } catch (e) {
                const img = new Image();
                await new Promise((res, rej) => { img.onload = res; img.onerror = rej; img.src = m[1]; });
                return true;
              }
            }"""
        )
        if not hero_ok:
            errors.append("Hero background image failed to load")

        page.locator("#checkin").fill("2026-08-02")
        page.locator("#checkout").fill("2026-08-06")
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(400)
        if not page.locator("#guestPanel.open").count():
            errors.append("Guest panel did not open")
        page.locator("#adultsPlus").click()
        page.locator("#childrenPlus").click()
        page.locator("#roomType").select_option("pooki")
        page.wait_for_timeout(300)

        for sel in ["#rooms", "#amenities", "#gallery", "#location", "#inquiry", "#trust"]:
            page.locator(sel).scroll_into_view_if_needed()
            page.wait_for_timeout(300)

        page.screenshot(path=str(ARTIFACTS / "rauma-studios-desktop.png"), full_page=True)

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.evaluate("window.scrollTo(0, 0)")
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        if not page.locator("#navMobile.open").count():
            errors.append("Mobile nav did not open")
        page.locator("#navClose").click()
        page.screenshot(path=str(ARTIFACTS / "rauma-studios-mobile.png"), full_page=True)

        browser.close()

    if errors:
        print("VERIFICATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print(f"All checks passed. Images checked: {len(imgs)}")


if __name__ == "__main__":
    main()
