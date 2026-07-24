#!/usr/bin/env python3
"""Verify WEIS prototype: images, inquiry form, layout at multiple viewports."""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)

results = {"images": [], "interactions": [], "errors": []}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(1000)

        # Force lazy-loaded images into view before checking
        page.evaluate(
            """async () => {
              const imgs = [...document.querySelectorAll('img')];
              for (const img of imgs) {
                img.scrollIntoView({ block: 'center' });
                await new Promise(r => setTimeout(r, 200));
                if (!img.complete) {
                  await new Promise(r => { img.onload = img.onerror = r; });
                }
              }
              window.scrollTo(0, 0);
            }"""
        )
        page.wait_for_timeout(800)

        imgs = page.locator("img").all()
        for img in imgs:
            src = img.get_attribute("src") or ""
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            results["images"].append({"src": src, "ok": ok})
            if not ok:
                results["errors"].append(f"Broken image: {src}")

        # Hero CSS background is not an <img>; spot-check brand + tagline
        brand = page.locator(".hero-brand").inner_text()
        tagline = page.locator(".hero-tagline").inner_text()
        if "Weis" not in brand:
            results["errors"].append(f"Missing brand in hero: {brand!r}")
        if "Wspaniałe przyjęcia" not in tagline:
            results["errors"].append(f"Missing tagline: {tagline!r}")
        results["interactions"].append(f"hero brand/tagline ok: {brand.split()[0]}")

        event_date = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+14); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#eventDate").fill(event_date)
        page.locator("#eventType").select_option("wesele")
        page.locator("#guests").fill("120")
        page.locator("#roomPref").select_option("krysztalowa")
        page.locator("#inquiryForm button[type=submit]").click()
        page.wait_for_timeout(400)
        toast = page.locator("#inquiryToast").inner_text()
        if "120" not in toast:
            results["errors"].append(f"Inquiry toast unexpected: {toast!r}")
        results["interactions"].append(f"inquiry form: {toast[:80]}")

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(800)
        page.screenshot(path=str(ARTIFACTS / "weis-desktop-full.png"), full_page=True)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(400)
        page.screenshot(path=str(ARTIFACTS / "weis-desktop-hero.png"))

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        page.screenshot(path=str(ARTIFACTS / "weis-mobile-menu.png"))
        page.locator("#navClose").click()

        page.locator("#zapytanie").scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        page.screenshot(path=str(ARTIFACTS / "weis-mobile-inquiry.png"))
        page.screenshot(path=str(ARTIFACTS / "weis-mobile-full.png"), full_page=True)

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
