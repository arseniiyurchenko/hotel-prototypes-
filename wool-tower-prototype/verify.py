#!/usr/bin/env python3
"""Verify Wool Tower prototype: images, anchors, viewing widget, mobile."""

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
        page = browser.new_page(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page.goto(URL, wait_until="networkidle", timeout=120000)
        page.wait_for_timeout(1200)

        page.evaluate(
            """async () => {
              const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
              for (let y = 0; y < document.body.scrollHeight; y += 500) {
                window.scrollTo(0, y);
                await sleep(120);
              }
              window.scrollTo(0, 0);
            }"""
        )
        page.wait_for_timeout(600)

        for img in page.locator("img").all():
            img.scroll_into_view_if_needed()
            src = img.get_attribute("src") or ""
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            results["images"].append({"src": src, "ok": ok})
            if not ok:
                results["errors"].append(f"Broken image: {src}")

        metrics = page.evaluate(
            """() => {
              const brand = document.querySelector('.brand').getBoundingClientRect();
              const cta = document.querySelector('.header-cta').getBoundingClientRect();
              return {
                logoLeft: brand.left,
                ctaRightGap: window.innerWidth - cta.right,
              };
            }"""
        )
        results["interactions"].append(f"header spacing: {metrics}")
        if metrics["logoLeft"] < 20 or metrics["ctaRightGap"] < 20:
            results["errors"].append(f"Cramped header spacing: {metrics}")

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(400)
        page.locator('.nav-desktop a[href="#spaces"]').click()
        page.wait_for_timeout(1500)
        check = page.evaluate(
            """() => {
              const sec = document.querySelector('#spaces');
              const header = document.querySelector('.site-header');
              const top = sec.getBoundingClientRect().top;
              const headerBottom = header.getBoundingClientRect().bottom;
              return { top, headerBottom, covered: top < headerBottom - 4, scrollY: window.scrollY };
            }"""
        )
        results["interactions"].append(f"smooth nav to #spaces: {check}")
        if check["covered"]:
            results["errors"].append(f"Spaces section covered by fixed header after nav: {check}")

        page.locator(".header-cta").click()
        page.wait_for_timeout(1000)
        page.locator("#viewingDate").fill("2026-09-15")
        page.locator("#preferredSeason").select_option("autumn")
        page.locator("#preferredYear").select_option("2027")
        before = page.locator("#guestCount").inner_text()
        page.locator("#guestsPlus").click()
        page.locator("#guestTrigger").click()
        after = page.locator("#guestCount").inner_text()
        page.locator("#viewingSubmit").click()
        status = page.locator("#widgetStatus").inner_text()
        results["interactions"].append(f"guests {before}->{after}; status={status}")
        if before == after:
            results["errors"].append("Guest selector did not change")
        if not status:
            results["errors"].append("Viewing widget submit produced no status")

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(400)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        if not page.locator("#navMobile.open").count():
            results["errors"].append("Mobile nav did not open")
        page.screenshot(path=str(ARTIFACTS / "wool-tower-verify-mobile.png"))

        browser.close()

    print(json.dumps(results, indent=2))
    if results["errors"]:
        print("ERRORS:", results["errors"])
        sys.exit(1)
    print("Verification passed.")


if __name__ == "__main__":
    main()
