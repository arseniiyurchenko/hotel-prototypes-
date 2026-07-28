#!/usr/bin/env python3
"""Verify Haus Anna prototype: images, booking widget, layout."""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)

results = {"images": [], "interactions": [], "errors": [], "layout": []}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2000)

        imgs = page.locator("img").all()
        for img in imgs:
            src = img.get_attribute("src") or ""
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            results["images"].append({"src": src, "ok": ok})
            if not ok:
                results["errors"].append(f"Broken image: {src}")

        # Hero background via computed style — check network
        hero_bg = page.evaluate(
            """() => {
              const el = document.querySelector('.hero-bg');
              const bg = getComputedStyle(el).backgroundImage;
              return bg;
            }"""
        )
        results["interactions"].append(f"hero background: {hero_bg[:120]}")

        tomorrow = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+1); return d.toISOString().split('T')[0]; }"
        )
        day_after = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+4); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#checkin").fill(tomorrow)
        page.locator("#checkout").fill(day_after)
        nights = page.locator("#nightsCount").inner_text()
        results["interactions"].append(f"date pickers filled; nights={nights}")

        page.locator("#guestTrigger").click()
        page.wait_for_timeout(300)
        page.locator("#adultsPlus").click()
        page.locator("#childrenPlus").click()
        summary = page.locator("#guestSummary").inner_text()
        chip = page.locator("#guestChip").inner_text()
        results["interactions"].append(f"guest selector: {summary} / chip: {chip}")

        page.locator("#roomType").select_option("twin-bf")
        page.locator("#bookingForm").evaluate("form => form.requestSubmit()")
        page.wait_for_timeout(400)
        result_text = page.locator("#bookingResult").inner_text()
        results["interactions"].append(f"search result: {result_text[:140]}")

        # Check sections exist and have height
        for sid in ["#rooms", "#amenities", "#gallery", "#location", "#trust"]:
            box = page.locator(sid).bounding_box()
            if not box or box["height"] < 80:
                results["errors"].append(f"Empty/collapsed section: {sid}")
            else:
                results["layout"].append({"section": sid, "height": box["height"]})

        page.screenshot(path=str(ARTIFACTS / "hausanna-desktop-hero.png"))
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(600)
        page.screenshot(path=str(ARTIFACTS / "hausanna-desktop-full.png"), full_page=True)

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.evaluate("window.scrollTo(0, 0)")
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        page.screenshot(path=str(ARTIFACTS / "hausanna-mobile-menu.png"))
        page.locator("#navClose").click()

        page.locator("#booking").scroll_into_view_if_needed()
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(300)
        page.screenshot(path=str(ARTIFACTS / "hausanna-mobile-booking.png"))
        page.screenshot(path=str(ARTIFACTS / "hausanna-mobile-full.png"), full_page=True)

        # Overlap check: ensure booking shell not covering hero brand excessively on mobile
        overlap = page.evaluate(
            """() => {
              const brand = document.querySelector('.brand-mark');
              const booking = document.querySelector('.booking-shell');
              if (!brand || !booking) return null;
              const a = brand.getBoundingClientRect();
              const b = booking.getBoundingClientRect();
              const overlapY = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
              return { brandBottom: a.bottom, bookingTop: b.top, overlapY };
            }"""
        )
        results["layout"].append({"overlap_check": overlap})

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
