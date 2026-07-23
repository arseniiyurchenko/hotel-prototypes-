#!/usr/bin/env python3
"""Record smooth walkthrough video of Hotel Ērgļi prototype."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "walkthrough-video-ergli"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def smooth_scroll(page, y, steps=28, pause=40):
    page.evaluate(
        """({ y, steps }) => new Promise((resolve) => {
          const start = window.scrollY;
          const delta = y - start;
          let i = 0;
          function frame() {
            i += 1;
            const t = i / steps;
            const eased = t < 0.5 ? 2*t*t : 1 - Math.pow(-2*t + 2, 2) / 2;
            window.scrollTo(0, start + delta * eased);
            if (i < steps) requestAnimationFrame(frame);
            else resolve();
          }
          requestAnimationFrame(frame);
        })""",
        {"y": y, "steps": steps},
    )
    page.wait_for_timeout(pause)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=str(VIDEO_DIR),
            record_video_size={"width": 1280, "height": 800},
        )
        page = context.new_page()
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2000)

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1200)

        # Smooth continuous scroll through page
        total = page.evaluate("() => document.body.scrollHeight - window.innerHeight")
        for frac in [0.12, 0.22, 0.35, 0.48, 0.62, 0.78, 0.92, 1.0]:
            smooth_scroll(page, int(total * frac), steps=36, pause=350)

        page.wait_for_timeout(600)
        page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' })")
        page.wait_for_timeout(1400)

        # Demonstrate smooth anchor navigation
        for href in ["#booking", "#rooms", "#amenities", "#gallery", "#location", "#trust"]:
            page.locator(f'.nav-desktop a[href="{href}"]').click()
            page.wait_for_timeout(1400)

        # Booking widget interaction
        page.locator("#booking").scroll_into_view_if_needed()
        page.wait_for_timeout(700)
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
        page.wait_for_timeout(700)
        page.locator("#adultsPlus").click()
        page.wait_for_timeout(400)
        page.locator("#childrenPlus").click()
        page.wait_for_timeout(500)
        page.locator("#roomType").select_option("suite")
        page.wait_for_timeout(700)
        page.mouse.click(200, 120)
        page.wait_for_timeout(500)

        # Mobile viewport
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(800)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(900)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(1100)
        page.locator("#navClose").click()
        page.wait_for_timeout(600)
        mobile_total = page.evaluate("() => document.body.scrollHeight - window.innerHeight")
        for frac in [0.2, 0.45, 0.7, 1.0]:
            smooth_scroll(page, int(mobile_total * frac), steps=30, pause=300)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "hotel-ergli-homepage-walkthrough.webm"
            Path(video_path).rename(dest)
            print(f"Video saved: {dest}")
        else:
            print("No video recorded")


if __name__ == "__main__":
    main()
