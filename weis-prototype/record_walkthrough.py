#!/usr/bin/env python3
"""Record a walkthrough video of the WEIS prototype."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/index.html"
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

        page.locator("#zapytanie").scroll_into_view_if_needed()
        page.wait_for_timeout(1000)

        event_date = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+21); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#eventDate").fill(event_date)
        page.wait_for_timeout(400)
        page.locator("#eventType").select_option("wesele")
        page.wait_for_timeout(400)
        page.locator("#guests").fill("180")
        page.wait_for_timeout(400)
        page.locator("#roomPref").select_option("krysztalowa")
        page.wait_for_timeout(500)
        page.locator("#inquiryForm button[type=submit]").click()
        page.wait_for_timeout(1000)

        for section in ["#o-nas", "#sale", "#udogodnienia", "#oferta", "#galeria", "#lokalizacja", "#kontakt"]:
            page.locator(section).scroll_into_view_if_needed()
            page.wait_for_timeout(1100)

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1200)

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(800)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(800)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(1000)
        page.locator("#navClose").click()
        page.wait_for_timeout(500)
        page.locator("#zapytanie").scroll_into_view_if_needed()
        page.wait_for_timeout(1000)
        page.locator("#sale").scroll_into_view_if_needed()
        page.wait_for_timeout(1200)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "weis-walkthrough.webm"
            Path(video_path).replace(dest)
            print(f"Walkthrough saved to {dest}")
        else:
            print("No video recorded")


if __name__ == "__main__":
    main()
