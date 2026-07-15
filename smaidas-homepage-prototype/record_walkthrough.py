#!/usr/bin/env python3
"""Record smooth walkthrough video of the Smaidas prototype."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "smaidas-walkthrough-raw"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def smooth_scroll_to(page, selector, duration_ms=1400):
    page.evaluate(
        """({ selector, durationMs }) => new Promise((resolve) => {
          const el = document.querySelector(selector);
          if (!el) { resolve(); return; }
          const header = document.querySelector('.site-header');
          const offset = (header ? header.offsetHeight : 0) + 8;
          const startY = window.scrollY;
          const targetY = Math.max(0, el.getBoundingClientRect().top + window.scrollY - offset);
          const dist = targetY - startY;
          const start = performance.now();
          function frame(now) {
            const t = Math.min(1, (now - start) / durationMs);
            const eased = t < 0.5 ? 2*t*t : -1+(4-2*t)*t;
            window.scrollTo(0, startY + dist * eased);
            if (t < 1) requestAnimationFrame(frame);
            else resolve();
          }
          requestAnimationFrame(frame);
        })""",
        {"selector": selector, "durationMs": duration_ms},
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
        page.wait_for_timeout(2200)

        # Hero linger
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1600)

        # Smooth continuous scroll through page
        for sel, ms in [
            ("#booking", 1600),
            ("#accommodation", 1800),
            ("#amenities", 1600),
            ("#gallery", 1600),
            ("#location", 1600),
            ("#trust", 1500),
            ("#footer", 1400),
        ]:
            smooth_scroll_to(page, sel, ms)
            page.wait_for_timeout(900)

        # Back to top, demonstrate smooth anchor nav
        page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' })")
        page.wait_for_timeout(1400)
        page.locator('.nav-desktop a[href="#accommodation"]').click()
        page.wait_for_timeout(1600)
        page.locator('a.header-cta').click()
        page.wait_for_timeout(1400)

        # Booking widget interaction
        tomorrow = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+3); return d.toISOString().split('T')[0]; }"
        )
        checkout = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+6); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#checkin").fill(tomorrow)
        page.wait_for_timeout(450)
        page.locator("#checkout").fill(checkout)
        page.wait_for_timeout(450)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(600)
        page.locator("#adultsPlus").click()
        page.wait_for_timeout(350)
        page.locator("#childrenPlus").click()
        page.wait_for_timeout(450)
        page.locator("#bookingForm button[type=submit]").click()
        page.wait_for_timeout(1000)
        page.mouse.click(200, 120)
        page.wait_for_timeout(400)

        # Continue smooth scroll through remaining sections
        for sel in ["#accommodation", "#amenities", "#gallery", "#location", "#trust"]:
            smooth_scroll_to(page, sel, 1300)
            page.wait_for_timeout(700)

        # Mobile viewport
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(700)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(900)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(900)
        page.locator('#navMobile a[href="#gallery"]').click()
        page.wait_for_timeout(1400)
        smooth_scroll_to(page, "#booking", 1200)
        page.wait_for_timeout(700)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(900)
        page.evaluate("window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })")
        page.wait_for_timeout(1600)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "smaidas-homepage-prototype-walkthrough.webm"
            Path(video_path).rename(dest)
            print(f"Video saved: {dest}")
        else:
            print("No video recorded")
            raise SystemExit(1)


if __name__ == "__main__":
    main()
