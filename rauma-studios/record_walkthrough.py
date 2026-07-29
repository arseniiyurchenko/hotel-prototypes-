#!/usr/bin/env python3
"""Record a walkthrough video of the Rauma Studios prototype."""

from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8767/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "rauma-walkthrough-video"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


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
        page.wait_for_timeout(1500)

        page.locator("#booking").scroll_into_view_if_needed()
        page.wait_for_timeout(1000)

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
        # Max 2 guests — decrease adults then add a child to show controls
        page.locator("#adultsMinus").click()
        page.wait_for_timeout(300)
        page.locator("#childrenPlus").click()
        page.wait_for_timeout(400)
        page.locator("#roomType").select_option("pooki")
        page.wait_for_timeout(600)
        page.mouse.click(400, 200)
        page.wait_for_timeout(400)

        page.locator("#bookingForm button[type='submit']").click()
        page.wait_for_timeout(800)
        page.on("dialog", lambda d: d.accept())
        # Re-bind after handler — submit may have already fired; dismiss if still open
        page.wait_for_timeout(500)

        for section in ["#rooms", "#amenities", "#gallery", "#location", "#inquiry", "#trust"]:
            page.locator(section).scroll_into_view_if_needed()
            page.wait_for_timeout(1200)

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(800)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(800)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(1000)
        page.locator("#navClose").click()
        page.wait_for_timeout(500)
        page.locator("#booking").scroll_into_view_if_needed()
        page.wait_for_timeout(800)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(1000)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        page.wait_for_timeout(1200)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "rauma-studios-prototype-walkthrough.webm"
            Path(video_path).rename(dest)
            print(f"Video saved: {dest}")
            print(f"Size: {dest.stat().st_size} bytes")
        else:
            print("No video recorded")
            raise SystemExit(1)


if __name__ == "__main__":
    main()
