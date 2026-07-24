#!/usr/bin/env python3
"""Record a walkthrough video of the Lingnerschloss prototype."""

from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8767/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "lingnerschloss-walkthrough-video"
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

        for section in ["#welcome", "#spaces", "#features", "#weddings", "#impressions", "#inquiry", "#location"]:
            page.locator(section).scroll_into_view_if_needed()
            page.wait_for_timeout(1100)

        page.locator("#name").fill("Alex Example")
        page.wait_for_timeout(400)
        page.locator("#email").fill("alex@example.com")
        page.wait_for_timeout(300)
        page.locator("#option").select_option(label="Meeting / conference")
        page.wait_for_timeout(400)
        page.locator("#request").fill("Interested in Sternensaal for a company reception.")
        page.wait_for_timeout(500)
        page.locator("#inquiryForm button[type=submit]").click()
        page.wait_for_timeout(1200)

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
        page.locator("#spaces").scroll_into_view_if_needed()
        page.wait_for_timeout(1000)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        page.wait_for_timeout(1200)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "lingnerschloss-walkthrough.webm"
            Path(video_path).replace(dest)
            print(f"Wrote {dest}")
        else:
            print("No video recorded")


if __name__ == "__main__":
    main()
