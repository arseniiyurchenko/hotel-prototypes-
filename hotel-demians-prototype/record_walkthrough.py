#!/usr/bin/env python3
"""Record smooth walkthrough video of Hotel Demians prototype."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "demians-walkthrough-raw"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def smooth_scroll(page, target_y, steps=40, step_delay=40):
    """Animate scroll continuously rather than jumping."""
    start = page.evaluate("() => window.scrollY")
    for i in range(1, steps + 1):
        y = start + (target_y - start) * (i / steps)
        page.evaluate(f"window.scrollTo(0, {y})")
        page.wait_for_timeout(step_delay)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=str(VIDEO_DIR),
            record_video_size={"width": 1280, "height": 800},
        )
        page = context.new_page()
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(2000)

        # Start at hero
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1500)

        # Smooth scroll into booking + interact
        booking_y = page.evaluate("() => document.getElementById('booking').offsetTop - 80")
        smooth_scroll(page, booking_y, steps=35, step_delay=35)
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
        page.wait_for_timeout(700)
        page.locator("#adultsPlus").click()
        page.wait_for_timeout(400)
        page.locator("#childrenPlus").click()
        page.wait_for_timeout(400)
        page.locator("#roomType").select_option("double")
        page.wait_for_timeout(600)
        page.mouse.click(200, 120)
        page.wait_for_timeout(500)

        # Demonstrate smooth anchor navigation (nav click)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(800)
        page.click('.nav-desktop a[href="#gallery"]')
        page.wait_for_timeout(1800)
        page.click('.nav-desktop a[href="#rooms"]')
        page.wait_for_timeout(1600)

        # Continuous scroll through remaining sections
        for section_id in ["amenities", "gallery", "location", "trust", "footer"]:
            y = page.evaluate(f"() => document.getElementById('{section_id}').offsetTop - 60")
            cur = page.evaluate("() => window.scrollY")
            steps = max(25, int(abs(y - cur) / 40))
            smooth_scroll(page, y, steps=min(steps, 55), step_delay=32)
            page.wait_for_timeout(900)

        # Mobile viewport
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(700)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(900)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(1100)
        page.locator("#navClose").click()
        page.wait_for_timeout(500)
        booking_y = page.evaluate("() => document.getElementById('booking').offsetTop - 40")
        smooth_scroll(page, booking_y, steps=30, step_delay=35)
        page.wait_for_timeout(600)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(1000)
        mid = page.evaluate("() => document.body.scrollHeight * 0.45")
        smooth_scroll(page, mid, steps=40, step_delay=30)
        page.wait_for_timeout(1200)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "demians-hotel-prototype-walkthrough.webm"
            Path(video_path).rename(dest)
            print(f"Video saved: {dest}")
            print(f"Size: {dest.stat().st_size} bytes")
        else:
            print("No video recorded")
            raise SystemExit(1)


if __name__ == "__main__":
    main()
