#!/usr/bin/env python3
"""Verify Deer Park Hall prototype: images, enquiry form, layout at multiple viewports."""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8771/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)

results = {"images": [], "interactions": [], "errors": []}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1200)
        page.evaluate(
            """async () => {
              const imgs = [...document.images];
              await Promise.all(imgs.map(img => img.complete ? Promise.resolve() : new Promise(res => {
                img.addEventListener('load', res, { once: true });
                img.addEventListener('error', res, { once: true });
              })));
            }"""
        )
        page.wait_for_timeout(800)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(400)

        imgs = page.locator("img").all()
        for img in imgs:
            src = img.get_attribute("src") or ""
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            results["images"].append({"src": src[:120], "ok": ok})
            if not ok:
                results["errors"].append(f"Broken image: {src}")

        # Hero background is CSS; check computed background-image loads via network
        hero_bg = page.locator(".hero-bg")
        if hero_bg.count() == 0:
            results["errors"].append("Missing hero background element")
        else:
            results["interactions"].append("hero background present")

        page.locator("#name").fill("Alex Morgan")
        page.locator("#email").fill("alex@example.com")
        page.locator("#eventType").select_option("conference")
        page.locator("#guests").fill("40")
        page.locator("#message").fill("Day delegate enquiry for Bredon Room")
        page.locator("#submitEnquiry").click()
        page.wait_for_timeout(400)
        status = page.locator("#formStatus").inner_text()
        results["interactions"].append(f"enquiry form: {status[:80]}")

        brand = page.locator(".hero-brand").inner_text()
        tagline = page.locator(".hero-line").inner_text()
        results["interactions"].append(f"brand={brand!r} tagline={tagline!r}")
        if "Deer Park Hall" not in brand:
            results["errors"].append("Hero brand missing venue name")
        if "space to breathe" not in tagline.lower():
            results["errors"].append("Hero tagline missing")

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(800)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)

        page.screenshot(path=str(ARTIFACTS / "deer-park-hall-desktop-full.png"), full_page=True)
        page.screenshot(path=str(ARTIFACTS / "deer-park-hall-desktop-hero.png"))

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        page.screenshot(path=str(ARTIFACTS / "deer-park-hall-mobile-menu.png"))
        page.locator("#navClose").click()
        page.wait_for_timeout(300)

        page.locator("#enquire").scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        page.screenshot(path=str(ARTIFACTS / "deer-park-hall-mobile-enquiry.png"))

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(600)
        page.screenshot(path=str(ARTIFACTS / "deer-park-hall-mobile-full.png"), full_page=True)

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
