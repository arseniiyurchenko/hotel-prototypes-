#!/usr/bin/env python3
"""Record a walkthrough video of the Hoffmanův dvůr prototype."""

from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8766/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "hoffman-walkthrough-video"
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

        for section in ["#objevte", "#prostory", "#akce", "#sluzby", "#galerie", "#reference", "#kontakt"]:
            page.locator(section).scroll_into_view_if_needed()
            page.wait_for_timeout(1200)

        page.locator("#name").fill("Anna Nováková")
        page.wait_for_timeout(400)
        page.locator("#email").fill("anna@example.com")
        page.wait_for_timeout(400)
        page.locator("#eventType").select_option("svatba")
        page.wait_for_timeout(400)
        page.locator("#message").fill("Poptávka svatby pro cca 80 hostů.")
        page.wait_for_timeout(500)
        page.locator("#inquiryForm button[type=submit]").click()
        page.wait_for_timeout(1200)

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1000)

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(800)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(1000)
        page.locator("#navClose").click()
        page.wait_for_timeout(600)

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)

        context.close()
        browser.close()

    videos = list(VIDEO_DIR.glob("*.webm"))
    if not videos:
        raise SystemExit("No walkthrough video recorded")
    target = ARTIFACTS / "hoffman-walkthrough.webm"
    videos[0].replace(target)
    print(f"Wrote {target}")


if __name__ == "__main__":
    main()
