#!/usr/bin/env python3
"""Record a walkthrough video of the Skrundas muiža hotel prototype."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8766/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "skrundas-walkthrough-video"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
REPO_VIDEO = Path(__file__).resolve().parent / "skrundas-muiza-prototype-walkthrough.webm"


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

        checkin = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+2); return d.toISOString().split('T')[0]; }"
        )
        checkout = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+5); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#checkin").fill(checkin)
        page.wait_for_timeout(500)
        page.locator("#checkout").fill(checkout)
        page.wait_for_timeout(500)
        page.locator("#guests").select_option("3")
        page.wait_for_timeout(400)
        page.locator("#rooms-count").select_option("2")
        page.wait_for_timeout(600)

        for section in ["#rooms", "#amenities", "#gallery", "#location", "#trust"]:
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
        page.locator("#menuClose").click()
        page.wait_for_timeout(500)
        page.locator("#booking").scroll_into_view_if_needed()
        page.wait_for_timeout(800)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        page.wait_for_timeout(1200)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "skrundas-muiza-prototype-walkthrough.webm"
            Path(video_path).rename(dest)
            REPO_VIDEO.write_bytes(dest.read_bytes())
            print(f"Video saved: {dest}")
            print(f"Repo copy: {REPO_VIDEO}")
        else:
            print("No video recorded")


if __name__ == "__main__":
    main()
