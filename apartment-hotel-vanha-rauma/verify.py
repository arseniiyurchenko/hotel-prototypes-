#!/usr/bin/env python3
"""Verify Vanha Rauma prototype: images, booking widget, layout at multiple viewports."""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8770/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)

results = {"images": [], "interactions": [], "errors": []}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(2000)

        imgs = page.locator("img").all()
        for img in imgs:
            src = img.get_attribute("src") or ""
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            results["images"].append({"src": src, "ok": ok})
            if not ok:
                results["errors"].append(f"Broken image: {src}")

        # Hero uses CSS background — check it loaded via network or computed style
        hero_bg = page.locator(".hero-bg").evaluate(
            "el => getComputedStyle(el).backgroundImage"
        )
        if "VanhaRaumanHuoneistohotelli.001" not in hero_bg:
            results["errors"].append(f"Hero background missing: {hero_bg}")
        else:
            results["interactions"].append("hero background present")

        checkin = page.locator("#checkin")
        checkout = page.locator("#checkout")
        tomorrow = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+1); return d.toISOString().split('T')[0]; }"
        )
        day_after = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+4); return d.toISOString().split('T')[0]; }"
        )
        checkin.fill(tomorrow)
        checkout.fill(day_after)
        results["interactions"].append("date pickers filled")

        page.locator("#guestTrigger").click()
        page.wait_for_timeout(300)
        if not page.locator("#guestDropdown.open").count():
            results["errors"].append("Guest panel did not open")
        page.locator("#adultsPlus").click()
        page.locator("#childrenPlus").click()
        summary = page.locator("#guestSummary").inner_text()
        results["interactions"].append(f"guest selector: {summary}")
        page.locator("#roomType").select_option("luksus")
        results["interactions"].append("room type selected: luksus")
        page.locator("#guestTrigger").click()

        for section in ["#rooms", "#amenities", "#gallery", "#location", "#trust"]:
            page.locator(section).scroll_into_view_if_needed()
            page.wait_for_timeout(250)

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(600)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(400)

        page.screenshot(path=str(ARTIFACTS / "vanharauma-desktop-full.png"), full_page=True)
        page.screenshot(path=str(ARTIFACTS / "vanharauma-desktop-hero.png"))

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        if not page.locator("#mobileNav.open").count():
            results["errors"].append("Mobile nav did not open")
        page.screenshot(path=str(ARTIFACTS / "vanharauma-mobile-menu.png"))
        page.locator("#navClose").click()
        page.wait_for_timeout(300)

        page.locator("#guestTrigger").scroll_into_view_if_needed()
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(300)
        page.screenshot(path=str(ARTIFACTS / "vanharauma-mobile-booking.png"))

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(600)
        page.screenshot(path=str(ARTIFACTS / "vanharauma-mobile-full.png"), full_page=True)

        context.close()
        browser.close()

    broken = [r for r in results["images"] if not r["ok"]]
    print(json.dumps(results, indent=2))
    print(f"\nImages: {len(results['images'])} total, {len(broken)} broken")
    if results["errors"]:
        print("ERRORS:", results["errors"])
        sys.exit(1)
    print("Verification passed.")


if __name__ == "__main__":
    main()
