#!/usr/bin/env python3
"""Verify Hotel Ludza prototype: images, widget, anchors, layout."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)


def main():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(URL, wait_until="networkidle", timeout=120000)
        page.wait_for_timeout(2500)

        # Images
        imgs = page.locator("img").all()
        for i, img in enumerate(imgs):
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            src = img.get_attribute("src") or ""
            if not ok:
                errors.append(f"Broken image [{i}]: {src}")

        # Header spacing from corners
        logo_box = page.locator(".logo").bounding_box()
        cta_box = page.locator(".header-cta").bounding_box()
        if not logo_box or logo_box["x"] < 24:
            errors.append(f"Logo too close to left edge: {logo_box}")
        if not cta_box or (1280 - (cta_box["x"] + cta_box["width"])) < 24:
            errors.append(f"CTA too close to right edge: {cta_box}")

        # Smooth scroll behavior
        behavior = page.evaluate("() => getComputedStyle(document.documentElement).scrollBehavior")
        if behavior != "smooth":
            errors.append(f"html scroll-behavior is '{behavior}', expected 'smooth'")

        # Anchor navigation
        for sel in ["#booking", "#rooms", "#amenities", "#gallery", "#location", "#trust"]:
            page.locator(f'.nav-desktop a[href="{sel}"]').click()
            page.wait_for_timeout(900)
            in_view = page.evaluate(
                """(id) => {
                  const el = document.querySelector(id);
                  if (!el) return false;
                  const r = el.getBoundingClientRect();
                  return r.top < window.innerHeight && r.bottom > 0;
                }""",
                sel,
            )
            if not in_view:
                errors.append(f"Section not in view after nav click: {sel}")

        # Footer section exists and is reachable via in-page link
        if not page.locator("#footer").count():
            errors.append("Missing #footer section")
        page.locator('a[href="#location"]').first.click()
        page.wait_for_timeout(600)

        # Booking widget
        page.locator("#booking").scroll_into_view_if_needed()
        page.locator("#checkin").fill("2026-08-05")
        page.locator("#checkout").fill("2026-08-08")
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(400)
        if not page.locator("#guestPanel.open").count():
            errors.append("Guest panel did not open")
        page.locator("#adultsPlus").click()
        page.locator("#childrenPlus").click()
        page.wait_for_timeout(300)
        summary = page.locator("#guestSummary").inner_text()
        if "3 adult" not in summary or "1 child" not in summary:
            errors.append(f"Guest summary unexpected: {summary}")
        page.locator("#searchBtn").click()
        page.wait_for_timeout(400)
        if page.locator("#searchFeedback").get_attribute("hidden") is not None:
            # hidden attribute absent means visible; if still present, fail
            if page.locator("#searchFeedback[hidden]").count():
                errors.append("Search feedback did not show")

        page.screenshot(path=str(ARTIFACTS / "hotel-ludza-desktop.png"), full_page=True)

        # Mobile
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.evaluate("window.scrollTo(0, 0)")
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        if not page.locator("#navMobile.open").count():
            errors.append("Mobile nav did not open")
        page.locator("#navClose").click()
        page.wait_for_timeout(300)
        page.screenshot(path=str(ARTIFACTS / "hotel-ludza-mobile.png"), full_page=True)

        browser.close()

    if errors:
        print("VERIFICATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
