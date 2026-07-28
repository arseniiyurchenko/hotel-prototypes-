#!/usr/bin/env python3
"""Verify Linnanpiha / Viipurin Puiston Majatalo prototype."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/linnanpiha-bed-breakfast/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)


def main():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2000)

        imgs = page.locator("img").all()
        print(f"Found {len(imgs)} img elements")
        for i, img in enumerate(imgs):
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            src = img.get_attribute("src") or ""
            nw = img.evaluate("el => el.naturalWidth")
            print(f"  [{i}] ok={ok} w={nw} {src[-80:]}")
            if not ok:
                errors.append(f"Broken image [{i}]: {src}")

        # hero background uses CSS url — fetch-check via evaluate
        hero_ok = page.evaluate(
            """async () => {
              const el = document.querySelector('.hero-bg');
              const bg = getComputedStyle(el).backgroundImage;
              const m = bg.match(/url\\(["']?(.*?)["']?\\)/);
              if (!m) return false;
              try {
                const r = await fetch(m[1], { method: 'HEAD', mode: 'cors' });
                return r.ok;
              } catch (e) {
                // CORS may block HEAD; try Image
                return await new Promise((resolve) => {
                  const img = new Image();
                  img.onload = () => resolve(img.naturalWidth > 0);
                  img.onerror = () => resolve(false);
                  img.src = m[1];
                });
              }
            }"""
        )
        print(f"Hero background loads: {hero_ok}")
        if not hero_ok:
            errors.append("Hero background image failed to load")

        page.locator("#checkin").fill("2026-08-05")
        page.locator("#checkout").fill("2026-08-08")
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(400)
        if not page.locator("#guestPanel.open").count():
            errors.append("Guest panel did not open")
        page.locator("#adultsPlus").click()
        page.locator("#childrenPlus").click()
        page.locator("#roomType").select_option("double")
        summary = page.locator("#guestSummary").inner_text()
        print(f"Guest summary: {summary}")
        if "2 adults" not in summary or "1 child" not in summary:
            errors.append(f"Unexpected guest summary: {summary}")

        for sel in ["#rooms", "#amenities", "#gallery", "#location", "#trust"]:
            page.locator(sel).scroll_into_view_if_needed()
            page.wait_for_timeout(300)

        overlaps = page.evaluate(
            """() => {
              const sections = [...document.querySelectorAll('section, footer, header')];
              const issues = [];
              for (const el of sections) {
                const r = el.getBoundingClientRect();
                if (r.height < 20) issues.push(el.id || el.className || el.tagName);
              }
              return issues;
            }"""
        )
        if overlaps:
            errors.append(f"Suspiciously short sections: {overlaps}")

        page.screenshot(path=str(ARTIFACTS / "linnanpiha-desktop.png"), full_page=True)

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.evaluate("window.scrollTo(0, 0)")
        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        if not page.locator("#navMobile.open").count():
            errors.append("Mobile nav did not open")
        page.locator("#navClose").click()
        page.wait_for_timeout(300)
        page.locator("#booking").scroll_into_view_if_needed()
        page.screenshot(path=str(ARTIFACTS / "linnanpiha-mobile.png"), full_page=True)

        browser.close()

    if errors:
        print("VERIFICATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
