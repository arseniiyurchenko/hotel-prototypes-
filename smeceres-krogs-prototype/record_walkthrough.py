#!/usr/bin/env python3
"""Record smooth walkthrough video of Smeceres Krogs prototype."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "smeceres-walkthrough-raw"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def smooth_scroll(page, y, steps=40, pause=40):
    start = page.evaluate("window.scrollY")
    for i in range(1, steps + 1):
        pos = start + (y - start) * (i / steps)
        page.evaluate(f"window.scrollTo(0, {pos})")
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
        page.goto(URL, wait_until="networkidle", timeout=120000)
        page.wait_for_timeout(2000)

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1500)

        # Smooth scroll into booking
        booking_y = page.locator("#booking").evaluate("el => el.getBoundingClientRect().top + window.scrollY - 80")
        smooth_scroll(page, booking_y, steps=35, pause=35)
        page.wait_for_timeout(800)

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
        page.locator("#roomType").select_option("triple")
        page.wait_for_timeout(600)
        page.mouse.click(200, 120)
        page.wait_for_timeout(500)

        # Demonstrate smooth nav anchor scroll
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(700)
        page.locator('.nav-desktop a[href="#rooms"]').click()
        page.wait_for_timeout(1400)
        page.locator('.nav-desktop a[href="#restaurant"]').click()
        page.wait_for_timeout(1400)
        page.locator('.nav-desktop a[href="#amenities"]').click()
        page.wait_for_timeout(1400)

        # Continuous smooth scroll through remaining sections
        for section in ["#gallery", "#location", "#trust", "#footer"]:
            y = page.locator(section).evaluate("el => el.getBoundingClientRect().top + window.scrollY - 60")
            smooth_scroll(page, y, steps=40, pause=30)
            page.wait_for_timeout(900)

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1200)

        # Mobile pass
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(800)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(800)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(1000)
        page.locator("#navClose").click()
        page.wait_for_timeout(500)
        smooth_scroll(page, 600, steps=25, pause=35)
        page.wait_for_timeout(800)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(1000)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        page.wait_for_timeout(1200)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "smeceres-krogs-prototype-walkthrough.webm"
            Path(video_path).rename(dest)
            print(f"Video saved: {dest}")
        else:
            print("No video recorded")


if __name__ == "__main__":
    main()
