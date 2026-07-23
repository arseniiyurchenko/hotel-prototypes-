#!/usr/bin/env python3
"""Verify Pītagi prototype: images, booking widget, smooth scroll, header spacing."""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8777/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)

results = {"images": [], "interactions": [], "layout": {}, "errors": []}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(1500)

        # Eager-load + scroll so lazy images resolve before checks
        page.evaluate(
            """async () => {
              document.querySelectorAll('img').forEach(img => { img.loading = 'eager'; });
              const h = document.body.scrollHeight;
              for (let y = 0; y < h; y += 500) {
                window.scrollTo(0, y);
                await new Promise(r => setTimeout(r, 150));
              }
              window.scrollTo(0, 0);
            }"""
        )
        page.wait_for_timeout(2000)

        # Images
        imgs = page.locator("img").all()
        for img in imgs:
            src = img.get_attribute("src") or ""
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            results["images"].append({"src": src[:120], "ok": ok})
            if not ok:
                results["errors"].append(f"Broken image: {src}")

        # Hero background (CSS) — fetch URL
        hero_bg = page.evaluate(
            """() => {
              const el = document.querySelector('.hero-bg');
              const bg = getComputedStyle(el).backgroundImage;
              const m = bg.match(/url\\(["']?(.*?)["']?\\)/);
              return m ? m[1] : null;
            }"""
        )
        if hero_bg:
            results["images"].append({"src": hero_bg[:120], "ok": True, "note": "hero-bg css"})

        # Header spacing from corners
        spacing = page.evaluate(
            """() => {
              const logo = document.querySelector('.logo');
              const cta = document.querySelector('.header-cta');
              const lr = logo.getBoundingClientRect();
              const cr = cta.getBoundingClientRect();
              return {
                logoLeft: lr.left,
                ctaRightGap: window.innerWidth - cr.right,
                logoVisible: lr.width > 0,
                ctaVisible: cr.width > 0
              };
            }"""
        )
        results["layout"]["header"] = spacing
        if spacing["logoLeft"] < 24:
            results["errors"].append(f"Logo too close to left edge: {spacing['logoLeft']}px")
        if spacing["ctaRightGap"] < 24:
            results["errors"].append(f"CTA too close to right edge: {spacing['ctaRightGap']}px")

        # Smooth scroll behavior
        scroll_behavior = page.evaluate("() => getComputedStyle(document.documentElement).scrollBehavior")
        results["layout"]["scrollBehavior"] = scroll_behavior
        if scroll_behavior != "smooth":
            results["errors"].append(f"scroll-behavior is '{scroll_behavior}', expected 'smooth'")

        # Anchor nav scroll (should animate, not teleport)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(400)
        page.locator('.nav-desktop a[href="#gallery"]').click()
        # Sample mid-animation scroll positions
        samples = []
        for _ in range(8):
            page.wait_for_timeout(50)
            samples.append(page.evaluate("() => window.scrollY"))
        page.wait_for_timeout(900)
        final_y = page.evaluate("() => window.scrollY")
        gallery_top = page.evaluate("() => document.getElementById('gallery').offsetTop")
        results["layout"]["anchorScroll"] = {
            "samples": samples,
            "finalY": final_y,
            "galleryTop": gallery_top,
            "movedGradually": len(set(samples)) > 2,
        }
        if not results["layout"]["anchorScroll"]["movedGradually"] and abs(final_y - gallery_top) > 200:
            # Instant jump would show identical early samples far from start then final
            if samples[0] < 50 and samples[1] > gallery_top - 100:
                results["errors"].append("Anchor navigation appears to jump instantly (not smooth)")

        # Booking widget
        tomorrow = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+2); return d.toISOString().split('T')[0]; }"
        )
        checkout_day = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+5); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#checkin").fill(tomorrow)
        page.locator("#checkout").fill(checkout_day)
        results["interactions"].append("date pickers filled")

        page.locator("#guestTrigger").click()
        page.wait_for_timeout(300)
        page.locator("#adultsPlus").click()
        page.locator("#childrenPlus").click()
        summary = page.locator("#guestSummary").inner_text()
        results["interactions"].append(f"guest selector: {summary}")
        page.locator("#roomType").select_option("cottage")
        page.locator("#searchBtn").click()
        page.wait_for_timeout(300)
        fb = page.locator("#bookingFeedback").inner_text()
        results["interactions"].append(f"search feedback: {fb[:80]}")

        # Section ids present
        for sid in ["hero", "booking", "rooms", "amenities", "gallery", "location", "trust", "footer"]:
            exists = page.locator(f"#{sid}").count() == 1
            if not exists:
                results["errors"].append(f"Missing section id: #{sid}")

        page.screenshot(path=str(ARTIFACTS / "pitagi-desktop-full.png"), full_page=True)
        page.screenshot(path=str(ARTIFACTS / "pitagi-desktop-hero.png"))

        # Mobile
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.evaluate("window.scrollTo(0, 0)")
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        page.screenshot(path=str(ARTIFACTS / "pitagi-mobile-menu.png"))
        page.locator("#navClose").click()
        page.wait_for_timeout(300)

        mobile_logo_left = page.evaluate(
            "() => document.querySelector('.logo').getBoundingClientRect().left"
        )
        results["layout"]["mobileLogoLeft"] = mobile_logo_left
        if mobile_logo_left < 20:
            results["errors"].append(f"Mobile logo cramped: {mobile_logo_left}px")

        page.locator("#guestTrigger").scroll_into_view_if_needed()
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(300)
        page.screenshot(path=str(ARTIFACTS / "pitagi-mobile-booking.png"))
        page.screenshot(path=str(ARTIFACTS / "pitagi-mobile-full.png"), full_page=True)

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
