#!/usr/bin/env python3
"""Record a smooth continuous walkthrough of the Saule prototype."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8770/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "saule-walkthrough-video"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def smooth_scroll_to(page, y, duration_ms=1400):
    page.evaluate(
        """([targetY, duration]) => {
          return new Promise((resolve) => {
            const startY = window.scrollY;
            const diff = targetY - startY;
            const start = performance.now();
            function step(now) {
              const t = Math.min(1, (now - start) / duration);
              const eased = t < 0.5 ? 2*t*t : -1+(4-2*t)*t;
              window.scrollTo(0, startY + diff * eased);
              if (t < 1) requestAnimationFrame(step);
              else resolve();
            }
            requestAnimationFrame(step);
          });
        }""",
        [y, duration_ms],
    )


def section_top(page, selector):
    return page.evaluate(
        """(sel) => {
          const el = document.querySelector(sel);
          if (!el) return 0;
          const rect = el.getBoundingClientRect();
          return window.scrollY + rect.top - 72;
        }""",
        selector,
    )


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=str(VIDEO_DIR),
            record_video_size={"width": 1280, "height": 800},
        )
        page = context.new_page()
        page.goto(URL, wait_until="networkidle", timeout=120000)
        page.wait_for_timeout(1800)

        # Hero hold
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1600)

        # Smooth scroll through sections
        for sel, dur in [
            ("#booking", 1600),
            ("#rooms", 1800),
            ("#amenities", 1700),
            ("#gallery", 1800),
            ("#location", 1600),
            ("#trust", 1600),
            ("#footer", 1500),
        ]:
            y = section_top(page, sel)
            smooth_scroll_to(page, max(0, y), dur)
            page.wait_for_timeout(900)

        # Back to top, demonstrate smooth anchor nav
        smooth_scroll_to(page, 0, 1200)
        page.wait_for_timeout(700)
        page.locator('.nav-desktop a[href="#rooms"]').click()
        page.wait_for_timeout(1400)
        page.locator('.nav-desktop a[href="#gallery"]').click()
        page.wait_for_timeout(1400)
        page.locator('.header-cta').click()
        page.wait_for_timeout(1200)

        # Booking widget interaction
        tomorrow = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+2); return d.toISOString().split('T')[0]; }"
        )
        checkout_day = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+5); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#checkin").fill(tomorrow)
        page.wait_for_timeout(500)
        page.locator("#checkout").fill(checkout_day)
        page.wait_for_timeout(500)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(600)
        page.locator("#adultsPlus").click()
        page.wait_for_timeout(400)
        page.locator("#childrenPlus").click()
        page.wait_for_timeout(400)
        page.locator("#roomType").select_option("superior")
        page.wait_for_timeout(700)
        page.mouse.click(200, 120)
        page.wait_for_timeout(500)

        # Continuous scroll to end
        total = page.evaluate("() => document.body.scrollHeight - window.innerHeight")
        smooth_scroll_to(page, total, 3200)
        page.wait_for_timeout(1000)

        # Mobile viewport
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(700)
        smooth_scroll_to(page, 0, 900)
        page.wait_for_timeout(700)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(1100)
        page.locator("#navClose").click()
        page.wait_for_timeout(500)
        y = section_top(page, "#booking")
        smooth_scroll_to(page, max(0, y), 1200)
        page.wait_for_timeout(600)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(1000)
        mid = page.evaluate("() => document.body.scrollHeight * 0.45")
        smooth_scroll_to(page, mid, 1800)
        page.wait_for_timeout(1000)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "saule-guesthouse-prototype-walkthrough.webm"
            Path(video_path).rename(dest)
            print(f"Video saved: {dest}")
        else:
            print("No video recorded")


if __name__ == "__main__":
    main()
