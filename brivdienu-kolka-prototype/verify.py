#!/usr/bin/env python3
"""Verify Brīvdienu Kolka prototype: images, booking widget, layout."""

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

        page.goto(URL, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(2000)

        imgs = page.locator("img").all()
        for img in imgs:
            src = img.get_attribute("src") or ""
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            results["images"].append({"src": src, "ok": ok})
            if not ok:
                results["errors"].append(f"Broken image: {src}")

        # Hero background is CSS — check it loaded via fetch
        hero_ok = page.evaluate(
            """async () => {
              const bg = getComputedStyle(document.querySelector('.hero-bg')).backgroundImage;
              const m = bg.match(/url\\(["']?(.*?)["']?\\)/);
              if (!m) return false;
              try {
                const r = await fetch(m[1], { method: 'HEAD', mode: 'no-cors' });
                return true;
              } catch (e) {
                const img = new Image();
                return await new Promise(res => {
                  img.onload = () => res(img.naturalWidth > 0);
                  img.onerror = () => res(false);
                  img.src = m[1];
                });
              }
            }"""
        )
        results["interactions"].append(f"hero background load probe: {hero_ok}")

        checkin = page.locator("#checkin")
        checkout = page.locator("#checkout")
        tomorrow = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+2); return d.toISOString().split('T')[0]; }"
        )
        day_after = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+5); return d.toISOString().split('T')[0]; }"
        )
        checkin.fill(tomorrow)
        checkout.fill(day_after)
        results["interactions"].append(f"dates: {tomorrow} → {day_after}")

        page.locator("#guestTrigger").click()
        page.wait_for_timeout(300)
        page.locator("#adultsPlus").click()
        page.locator("#childrenPlus").click()
        summary = page.locator("#guestSummary").inner_text()
        results["interactions"].append(f"guest selector: {summary}")
        if "3 adults" not in summary or "1 child" not in summary:
            results["errors"].append(f"Unexpected guest summary: {summary}")
        page.locator("#guestTrigger").click()

        for section in ["#rooms", "#amenities", "#gallery", "#location", "#trust", "#contact"]:
            page.locator(section).scroll_into_view_if_needed()
            page.wait_for_timeout(200)

        page.screenshot(path=str(ARTIFACTS / "brivdienu-kolka-desktop-full.png"), full_page=True)

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.evaluate("window.scrollTo(0, 0)")
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        page.screenshot(path=str(ARTIFACTS / "brivdienu-kolka-mobile-menu.png"))
        page.locator("#navClose").click()
        page.wait_for_timeout(300)

        page.locator("#booking").scroll_into_view_if_needed()
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(300)
        page.screenshot(path=str(ARTIFACTS / "brivdienu-kolka-mobile-booking.png"))

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(600)
        page.screenshot(path=str(ARTIFACTS / "brivdienu-kolka-mobile-full.png"), full_page=True)

        # Overlap / empty section checks
        for sel in ["#rooms", "#amenities", "#gallery", "#location", "#trust"]:
            box = page.locator(sel).bounding_box()
            if not box or box["height"] < 80:
                results["errors"].append(f"Section too small or missing: {sel}")

        context.close()
        browser.close()

    out = ARTIFACTS / "brivdienu-kolka-verify.json"
    out.write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    if results["errors"]:
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()
