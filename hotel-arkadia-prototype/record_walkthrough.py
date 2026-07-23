#!/usr/bin/env python3
"""Record smooth walkthrough video of Hotel Arkadia prototype."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/hotel-arkadia-prototype/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "arkadia-walkthrough-raw"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def smooth_scroll(page, y, steps=28, pause_ms=40):
    page.evaluate(
        """([targetY, steps]) => new Promise((resolve) => {
          const start = window.scrollY;
          const delta = targetY - start;
          let i = 0;
          function tick() {
            i += 1;
            const t = i / steps;
            const eased = t < 0.5 ? 2*t*t : -1 + (4 - 2*t)*t;
            window.scrollTo(0, start + delta * eased);
            if (i < steps) requestAnimationFrame(tick);
            else resolve();
          }
          requestAnimationFrame(tick);
        })""",
        [y, steps],
    )
    page.wait_for_timeout(steps * pause_ms // 4)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=str(VIDEO_DIR),
            record_video_size={"width": 1280, "height": 800},
        )
        page = context.new_page()
        page.goto(URL, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(1800)

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1200)

        # Demonstrate smooth anchor navigation
        page.locator('.nav-desktop a[href="#rooms"]').click()
        page.wait_for_timeout(1600)
        page.locator('.nav-desktop a[href="#amenities"]').click()
        page.wait_for_timeout(1400)
        page.locator('.header-cta').click()
        page.wait_for_timeout(1400)

        # Booking widget
        tomorrow = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+2); return d.toISOString().split('T')[0]; }"
        )
        checkout = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+5); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#checkin").fill(tomorrow)
        page.wait_for_timeout(500)
        page.locator("#checkout").fill(checkout)
        page.wait_for_timeout(500)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(600)
        page.locator("#adultsPlus").click()
        page.wait_for_timeout(350)
        page.locator("#childrenPlus").click()
        page.wait_for_timeout(450)
        page.locator("#roomPref").select_option("balcony")
        page.wait_for_timeout(500)
        page.mouse.click(400, 180)
        page.wait_for_timeout(400)
        page.locator("#searchBtn").click()
        page.wait_for_timeout(1200)

        # Continuous scroll through remaining sections
        height = page.evaluate("() => document.body.scrollHeight")
        positions = [0.22, 0.38, 0.52, 0.68, 0.82, 0.96]
        for frac in positions:
            smooth_scroll(page, int(height * frac), steps=36)
            page.wait_for_timeout(700)

        # Mobile pass
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(700)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(800)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(1000)
        page.locator('#navMobile a[href="#gallery"]').click()
        page.wait_for_timeout(1400)
        smooth_scroll(page, page.evaluate("() => document.body.scrollHeight * 0.55"), steps=30)
        page.wait_for_timeout(900)
        smooth_scroll(page, page.evaluate("() => document.body.scrollHeight * 0.95"), steps=30)
        page.wait_for_timeout(1000)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "hotel-arkadia-prototype-walkthrough.webm"
            Path(video_path).rename(dest)
            print(f"Video saved: {dest}")
        else:
            print("No video recorded")
            raise SystemExit(1)


if __name__ == "__main__":
    main()
