#!/usr/bin/env python3
"""Verify The Great Barn prototype: images, enquiry widget, nav, layout."""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8772/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)

results = {"images": [], "interactions": [], "errors": [], "checks": []}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(2000)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1800)
        page.evaluate(
            """async () => {
              const imgs = [...document.images];
              await Promise.all(imgs.map(img => img.complete ? Promise.resolve() : new Promise(res => {
                img.addEventListener('load', res, { once: true });
                img.addEventListener('error', res, { once: true });
              })));
            }"""
        )
        page.wait_for_timeout(1000)
        page.evaluate("window.scrollTo({ top: 0, behavior: 'instant' })")
        page.wait_for_timeout(400)

        imgs = page.locator("img").all()
        for img in imgs:
            src = img.get_attribute("src") or ""
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            results["images"].append({"src": src[:140], "ok": ok})
            if not ok:
                results["errors"].append(f"Broken image: {src}")

        # Hero CSS background
        hero_ok = page.evaluate(
            """() => {
              const el = document.querySelector('.hero-bg');
              if (!el) return false;
              const bg = getComputedStyle(el).backgroundImage;
              return bg && bg !== 'none' && bg.includes('url(');
            }"""
        )
        results["checks"].append({"hero_bg": hero_ok})
        if not hero_ok:
            results["errors"].append("Hero background image missing")

        # Header corner spacing
        spacing = page.evaluate(
            """() => {
              const header = document.querySelector('.site-header');
              const logo = document.querySelector('.logo');
              const cta = document.querySelector('.header-cta');
              const hr = header.getBoundingClientRect();
              const lr = logo.getBoundingClientRect();
              const cr = cta.getBoundingClientRect();
              return {
                logoLeft: Math.round(lr.left - hr.left),
                ctaRight: Math.round(hr.right - cr.right),
                logoTop: Math.round(lr.top - hr.top)
              };
            }"""
        )
        results["checks"].append({"header_spacing": spacing})
        if spacing["logoLeft"] < 16 or spacing["ctaRight"] < 16:
            results["errors"].append(f"Cramped header spacing: {spacing}")

        # Smooth scroll via nav anchors — start from true top
        page.evaluate("window.scrollTo({ top: 0, behavior: 'instant' })")
        page.wait_for_timeout(200)
        scroll_behavior = page.evaluate("() => getComputedStyle(document.documentElement).scrollBehavior")
        results["checks"].append({"scrollBehavior": scroll_behavior})
        if scroll_behavior != "smooth":
            results["errors"].append(f"scroll-behavior is {scroll_behavior!r}, expected smooth")

        start_y = page.evaluate("() => window.scrollY")
        page.locator('.nav-desktop a[href="#spaces"]').click()
        page.wait_for_timeout(350)
        mid_y = page.evaluate("() => window.scrollY")
        page.wait_for_timeout(1100)
        end_y = page.evaluate("() => window.scrollY")
        results["interactions"].append(f"nav spaces scroll: {start_y} -> {mid_y} -> {end_y}")
        if start_y > 5:
            results["errors"].append(f"Expected to start nav test at top, got y={start_y}")
        if end_y <= start_y + 50:
            results["errors"].append("Nav anchor to #spaces did not scroll")
        if mid_y <= start_y or mid_y >= end_y:
            # mid should be between start and end during smooth animation
            results["checks"].append({"smooth_mid_ok": False, "note": "mid sample may have finished early"})
        else:
            results["checks"].append({"smooth_mid_ok": True})
        spaces_top = page.evaluate("() => document.querySelector('#spaces').getBoundingClientRect().top")
        results["checks"].append({"spaces_top_after_nav": round(spaces_top)})
        if abs(spaces_top) > 140:
            results["errors"].append(f"#spaces not near viewport after nav (top={spaces_top})")

        # Enquiry widget: dates + guest selector
        page.locator("#enquire").scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        page.locator("#name").fill("Alex Morgan")
        page.locator("#email").fill("alex@example.com")
        event_day = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+30); return d.toISOString().slice(0,10); }"
        )
        view_day = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+10); return d.toISOString().slice(0,10); }"
        )
        page.locator("#eventDate").fill(event_day)
        page.locator("#viewingDate").fill(view_day)
        page.locator("#eventType").select_option("wedding")
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(300)
        if not page.locator("#guestPanel.open").count():
            results["errors"].append("Guest panel did not open")
        page.locator("#ceremonyPlus").click()
        page.wait_for_timeout(200)
        page.locator("#eveningPlus").click()
        page.wait_for_timeout(200)
        summary = page.locator("#guestSummary").inner_text()
        results["interactions"].append(f"guest summary: {summary}")
        page.locator("#message").fill("Saturday hire enquiry for June")
        page.locator("#submitEnquiry").click()
        page.wait_for_timeout(400)
        status = page.locator("#formStatus").inner_text()
        results["interactions"].append(f"enquiry form: {status[:100]}")
        if "does not send" not in status.lower() and "prototype" not in status.lower():
            results["errors"].append(f"Unexpected form status: {status}")

        brand = page.locator(".hero-brand").inner_text()
        if "The Great Barn" not in brand:
            results["errors"].append("Hero brand missing venue name")

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(400)
        page.screenshot(path=str(ARTIFACTS / "great-barn-desktop-hero.png"))
        page.screenshot(path=str(ARTIFACTS / "great-barn-desktop-full.png"), full_page=True)

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        if not page.locator("#navMobile.open").count():
            results["errors"].append("Mobile nav did not open")
        page.screenshot(path=str(ARTIFACTS / "great-barn-mobile-menu.png"))
        page.locator("#navClose").click()
        page.wait_for_timeout(300)
        page.locator("#enquire").scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(300)
        page.screenshot(path=str(ARTIFACTS / "great-barn-mobile-enquiry.png"))
        page.screenshot(path=str(ARTIFACTS / "great-barn-mobile-full.png"), full_page=True)

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
