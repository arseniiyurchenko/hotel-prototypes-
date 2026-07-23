#!/usr/bin/env python3
"""Verify Hotel Talsi prototype: images, booking widget, layout, smooth scroll."""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8770/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)

results = {"images": [], "interactions": [], "layout": [], "errors": []}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        page.goto(URL, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(2000)

        # Images
        imgs = page.locator("img").all()
        for img in imgs:
            src = img.get_attribute("src") or ""
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            results["images"].append({"src": src, "ok": ok})
            if not ok:
                results["errors"].append(f"Broken image: {src}")

        # Hero background image load check via computed style fetch
        hero_ok = page.evaluate(
            """async () => {
              const el = document.querySelector('.hero-bg');
              if (!el) return false;
              const bg = getComputedStyle(el).backgroundImage;
              const m = bg.match(/url\\(["']?(.*?)["']?\\)/);
              if (!m) return false;
              try {
                const r = await fetch(m[1], { method: 'HEAD', mode: 'cors' });
                return r.ok;
              } catch (e) {
                // CORS may block HEAD; try image element
                return await new Promise(resolve => {
                  const i = new Image();
                  i.onload = () => resolve(true);
                  i.onerror = () => resolve(false);
                  i.src = m[1];
                });
              }
            }"""
        )
        results["images"].append({"src": "hero-bg", "ok": hero_ok})
        if not hero_ok:
            results["errors"].append("Hero background image failed to load")

        # Header spacing from corners
        spacing = page.evaluate(
            """() => {
              const header = document.querySelector('.header-inner');
              const brand = document.querySelector('.brand');
              const cta = document.querySelector('.header-cta');
              const hr = header.getBoundingClientRect();
              const br = brand.getBoundingClientRect();
              const cr = cta.getBoundingClientRect();
              return {
                leftGap: br.left,
                rightGap: window.innerWidth - cr.right,
                logoOk: br.left >= 24,
                ctaOk: (window.innerWidth - cr.right) >= 24
              };
            }"""
        )
        results["layout"].append(spacing)
        if not spacing["logoOk"]:
            results["errors"].append(f"Logo too close to left edge: {spacing['leftGap']}px")
        if not spacing["ctaOk"]:
            results["errors"].append(f"CTA too close to right edge: {spacing['rightGap']}px")

        # Smooth scroll behavior
        scroll_behavior = page.evaluate("() => getComputedStyle(document.documentElement).scrollBehavior")
        results["interactions"].append(f"scroll-behavior: {scroll_behavior}")
        if scroll_behavior != "smooth":
            results["errors"].append("html scroll-behavior is not smooth")

        # Anchor nav smooth scroll demo
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(300)
        page.locator('.nav-desktop a[href="#amenities"]').click()
        page.wait_for_timeout(900)
        amenities_top = page.evaluate("() => document.getElementById('amenities').getBoundingClientRect().top")
        results["interactions"].append(f"after amenities click, section top≈{amenities_top:.0f}")
        if abs(amenities_top) > 160:
            # sticky header offset — allow some room; fail if clearly not near section
            if amenities_top > 400 or amenities_top < -200:
                results["errors"].append(f"Amenities anchor did not scroll near section (top={amenities_top})")

        # Booking widget
        tomorrow = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+1); return d.toISOString().split('T')[0]; }"
        )
        day_after = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+3); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#checkin").fill(tomorrow)
        page.locator("#checkout").fill(day_after)
        results["interactions"].append("date pickers filled")

        page.locator("#guestTrigger").click()
        page.wait_for_timeout(300)
        if not page.locator("#guestDropdown.open").count():
            results["errors"].append("Guest dropdown did not open")
        page.locator("#adultsPlus").click()
        page.locator("#childrenPlus").click()
        summary = page.locator("#guestSummary").inner_text()
        results["interactions"].append(f"guest selector: {summary}")
        page.mouse.click(20, 200)
        page.wait_for_timeout(200)

        # Section ids present
        for sid in ["hero", "booking", "rooms", "amenities", "gallery", "location", "trust", "footer"]:
            if page.locator(f"#{sid}").count() == 0:
                results["errors"].append(f"Missing section id=#{sid}")

        page.screenshot(path=str(ARTIFACTS / "hotel-talsi-desktop.png"), full_page=True)

        # Mobile
        page.set_viewport_size({"width": 390, "height": 844})
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(600)
        mobile_spacing = page.evaluate(
            """() => {
              const brand = document.querySelector('.brand');
              const cta = document.querySelector('.header-cta');
              const toggle = document.querySelector('#menuToggle');
              const br = brand.getBoundingClientRect();
              const cr = cta.getBoundingClientRect();
              const tr = toggle.getBoundingClientRect();
              return {
                leftGap: br.left,
                rightGap: window.innerWidth - tr.right,
                logoOk: br.left >= 16,
                ctaVisible: cr.width > 0 && cr.right <= window.innerWidth - 8,
                toggleOk: tr.right <= window.innerWidth - 8 && tr.left >= 0,
                toggleRect: {left: tr.left, right: tr.right},
                ctaRect: {left: cr.left, right: cr.right, width: cr.width}
              };
            }"""
        )
        results["layout"].append({"mobile": mobile_spacing})
        if not mobile_spacing["logoOk"] or not mobile_spacing["toggleOk"] or not mobile_spacing["ctaVisible"]:
            results["errors"].append(f"Mobile header cramped: {mobile_spacing}")

        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        page.screenshot(path=str(ARTIFACTS / "hotel-talsi-mobile-menu.png"))
        page.locator("#navClose").click()
        page.wait_for_timeout(300)

        page.locator("#booking").scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        page.locator("#guestTrigger").click(force=True)
        page.wait_for_timeout(300)
        page.screenshot(path=str(ARTIFACTS / "hotel-talsi-mobile-booking.png"))

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(600)
        page.screenshot(path=str(ARTIFACTS / "hotel-talsi-mobile-full.png"), full_page=True)

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
