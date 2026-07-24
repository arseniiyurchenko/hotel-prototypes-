#!/usr/bin/env python3
"""Record walkthrough video of Auchen Castle prototype."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8772/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "walkthrough-video"
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
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(2000)

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1500)

        page.locator("#inquiry").scroll_into_view_if_needed()
        page.wait_for_timeout(1000)

        event_date = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+21); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#eventDate").fill(event_date)
        page.wait_for_timeout(400)
        page.locator("#delegateBand").select_option(label="51 to 75")
        page.wait_for_timeout(400)
        page.locator("#eventType").select_option(label="Conference / meeting")
        page.wait_for_timeout(400)
        page.locator("#packageInterest").select_option(label="Day Delegate (£45 pp)")
        page.wait_for_timeout(500)
        page.locator("#inquiryForm button[type='submit']").click()
        page.wait_for_timeout(800)

        for section in ["#spaces", "#features", "#packages", "#gallery", "#location", "#contact"]:
            page.locator(section).scroll_into_view_if_needed()
            page.wait_for_timeout(1200)

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(800)

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(600)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(900)
        page.locator("#navClose").click()
        page.wait_for_timeout(600)

        context.close()
        browser.close()

    videos = list(VIDEO_DIR.glob("*.webm"))
    if not videos:
        raise SystemExit("No walkthrough video recorded")
    latest = max(videos, key=lambda p: p.stat().st_mtime)
    dest = ARTIFACTS / "auchen-castle-walkthrough.webm"
    latest.replace(dest)
    print(f"Walkthrough saved to {dest}")


if __name__ == "__main__":
    main()
