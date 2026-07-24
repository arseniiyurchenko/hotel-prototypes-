#!/usr/bin/env python3
"""Record a walkthrough video of the Hulme Hall prototype."""

from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "hulme-hall-walkthrough-video"
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
        page.wait_for_timeout(1200)

        for section in ["#about", "#rooms", "#amenities", "#gallery", "#weddings", "#pricing", "#contact"]:
            page.locator(section).scroll_into_view_if_needed()
            page.wait_for_timeout(900)

        page.locator("#enquiryName").fill("Alex Example")
        page.wait_for_timeout(300)
        page.locator("#enquiryEmail").fill("alex@example.com")
        page.wait_for_timeout(300)
        page.locator("#enquiryEvent").select_option("Wedding")
        page.wait_for_timeout(300)
        page.locator("#enquiryMessage").fill("Saturday reception enquiry for around 120 guests.")
        page.wait_for_timeout(800)

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1000)

        context.close()
        browser.close()

    videos = list(VIDEO_DIR.glob("*.webm"))
    if not videos:
        raise SystemExit("No walkthrough video recorded")
    dest = ARTIFACTS / "hulme-hall-walkthrough.webm"
    videos[0].replace(dest)
    print(f"Wrote {dest}")


if __name__ == "__main__":
    main()
