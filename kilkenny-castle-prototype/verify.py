#!/usr/bin/env python3
"""Verify Kilkenny Castle prototype: images, enquiry form, layout at multiple viewports."""

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
        page.wait_for_timeout(1500)

        event_date = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+21); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#eventDate").fill(event_date)
        page.locator("#eventType").select_option("conference")
        page.locator("#venueSpace").select_option("parade-tower")
        page.locator("#guests").fill("80")
        results["interactions"].append("enquiry fields filled")

        page.locator("#enquiryForm button[type=submit]").click()
        page.wait_for_timeout(400)
        toast_visible = page.locator("#enquiryToast").evaluate(
            "el => el.classList.contains('show')"
        )
        results["interactions"].append(f"enquiry toast shown: {toast_visible}")
        if not toast_visible:
            results["errors"].append("Enquiry toast did not show")

        for section in ["#spaces", "#amenities", "#gallery", "#location", "#rates", "#contact"]:
            page.locator(section).scroll_into_view_if_needed()
            page.wait_for_timeout(500)

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(800)

        # Force-load lazy images, then re-check dimensions
        page.evaluate(
            """() => {
              document.querySelectorAll('img[loading=lazy]').forEach(img => {
                img.loading = 'eager';
                if (!img.complete) {
                  const s = img.src; img.src = ''; img.src = s;
                }
              });
            }"""
        )
        page.wait_for_timeout(2500)

        imgs = page.locator("img").all()
        for img in imgs:
            src = img.get_attribute("src") or ""
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            results["images"].append({"src": src, "ok": ok})
            if not ok:
                results["errors"].append(f"Broken image: {src}")

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(400)

        page.screenshot(
            path=str(ARTIFACTS / "kilkenny-desktop-full.png"), full_page=True
        )

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        page.screenshot(path=str(ARTIFACTS / "kilkenny-mobile-menu.png"))
        page.locator("#navClose").click()
        page.wait_for_timeout(300)

        page.locator("#enquiry").scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        page.screenshot(path=str(ARTIFACTS / "kilkenny-mobile-enquiry.png"))

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(600)
        page.screenshot(
            path=str(ARTIFACTS / "kilkenny-mobile-full.png"), full_page=True
        )

        context.close()
        browser.close()

    out = ARTIFACTS / "kilkenny-verify.json"
    out.write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    if results["errors"]:
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()
