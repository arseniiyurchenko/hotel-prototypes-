#!/usr/bin/env python3
"""Verify The Great Barn prototype: images, enquiry form, layout at multiple viewports."""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8772/index.html"
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
        page.wait_for_timeout(1500)
        page.evaluate(
            """async () => {
              const imgs = [...document.images];
              await Promise.all(imgs.map(img => img.complete ? Promise.resolve() : new Promise(res => {
                img.addEventListener('load', res, { once: true });
                img.addEventListener('error', res, { once: true });
              })));
            }"""
        )
        page.wait_for_timeout(1200)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(400)

        imgs = page.locator("img").all()
        for img in imgs:
            src = img.get_attribute("src") or ""
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            results["images"].append({"src": src[:140], "ok": ok})
            if not ok:
                results["errors"].append(f"Broken image: {src}")

        hero_bg = page.locator(".hero-bg")
        if hero_bg.count() == 0:
            results["errors"].append("Missing hero background element")
        else:
            results["interactions"].append("hero background present")

        page.locator("#name").fill("Alex Morgan")
        page.locator("#email").fill("alex@example.com")
        page.locator("#eventType").select_option("wedding")
        page.locator("#guests").fill("120")
        page.locator("#message").fill("Viewing request for a Saturday in June")
        page.locator("#submitEnquiry").click()
        page.wait_for_timeout(400)
        status = page.locator("#formStatus").inner_text()
        results["interactions"].append(f"enquiry form: {status[:100]}")
        if "prototype" not in status.lower() and "does not send" not in status.lower():
            results["errors"].append(f"Unexpected form status: {status}")

        brand = page.locator(".hero-brand").inner_text()
        line = page.locator(".hero-line").inner_text()
        results["interactions"].append(f"brand={brand!r} line={line!r}")
        if "The Great Barn" not in brand:
            results["errors"].append("Hero brand missing venue name")
        if "grandeur" not in line.lower():
            results["errors"].append("Hero positioning line missing")

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
        page.screenshot(path=str(ARTIFACTS / "great-barn-mobile-enquiry.png"))

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(600)
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
