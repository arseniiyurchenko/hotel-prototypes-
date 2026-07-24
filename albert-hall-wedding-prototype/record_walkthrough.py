#!/usr/bin/env python3
"""Record smooth-scroll walkthrough video of the Albert Hall prototype."""

import math
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8777/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "albert-hall-walkthrough-video"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def smooth_scroll_to(page, target_y, duration_ms=1800, steps=60):
    start_y = page.evaluate("window.scrollY")
    delta = target_y - start_y
    if abs(delta) < 2:
        page.wait_for_timeout(duration_ms)
        return
    for i in range(1, steps + 1):
        t = i / steps
        eased = 0.5 - 0.5 * math.cos(math.pi * t)
        y = start_y + delta * eased
        page.evaluate("(y) => window.scrollTo(0, y)", y)
        page.wait_for_timeout(max(1, duration_ms // steps))


def scroll_to_section(page, selector, duration_ms=2000):
    box = page.locator(selector).evaluate(
        """(el) => {
            const header = document.getElementById('header');
            const offset = header ? header.offsetHeight + 8 : 0;
            return el.getBoundingClientRect().top + window.scrollY - offset;
        }"""
    )
    smooth_scroll_to(page, max(0, box), duration_ms=duration_ms)


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

        scroll_to_section(page, "#booking", 1800)
        page.wait_for_timeout(800)

        event_date = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+30); return d.toISOString().split('T')[0]; }"
        )
        alt_date = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+45); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#eventDate").fill(event_date)
        page.wait_for_timeout(500)
        page.locator("#altDate").fill(alt_date)
        page.wait_for_timeout(500)

        page.locator("#guestTrigger").click()
        page.wait_for_timeout(600)
        page.locator("#guestsPlus").click()
        page.wait_for_timeout(400)
        page.locator("#guestsPlus").click()
        page.wait_for_timeout(400)
        page.locator("#spaceType").select_option("great-hall")
        page.wait_for_timeout(600)
        page.mouse.click(400, 200)
        page.wait_for_timeout(500)

        for section in ["#about", "#spaces", "#amenities", "#gallery", "#location", "#testimonials", "#contact"]:
            scroll_to_section(page, section, 2200)
            page.wait_for_timeout(1000)

        smooth_scroll_to(page, page.evaluate("document.body.scrollHeight"), 2500)
        page.wait_for_timeout(1200)

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(800)
        page.locator('.nav-desktop a[href="#amenities"]').click()
        page.wait_for_timeout(2200)
        page.locator('.nav-desktop a[href="#gallery"]').click()
        page.wait_for_timeout(2200)
        page.locator('.header-cta').click()
        page.wait_for_timeout(1800)

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(800)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(800)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(1000)
        page.locator("#navClose").click()
        page.wait_for_timeout(500)

        smooth_scroll_to(page, page.evaluate("document.body.scrollHeight / 2"), 2000)
        page.wait_for_timeout(800)
        page.locator("#guestTrigger").scroll_into_view_if_needed()
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(1000)
        smooth_scroll_to(page, page.evaluate("document.body.scrollHeight"), 1800)
        page.wait_for_timeout(1200)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "albert-hall-wedding-prototype-walkthrough.webm"
            Path(video_path).rename(dest)
            print(f"Video saved: {dest}")
        else:
            print("No video recorded")


if __name__ == "__main__":
    main()
