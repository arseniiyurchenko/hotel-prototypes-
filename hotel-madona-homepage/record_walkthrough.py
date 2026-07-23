#!/usr/bin/env python3
"""Record smooth walkthrough video of Hotel Madona prototype."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "walkthrough-video-madona"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def smooth_scroll_to(page, y, steps=28, pause=40):
    page.evaluate(
        """({y, steps}) => new Promise((resolve) => {
          const start = window.scrollY;
          const delta = y - start;
          let i = 0;
          const tick = () => {
            i += 1;
            const t = i / steps;
            const eased = t < 0.5 ? 2*t*t : -1+(4-2*t)*t;
            window.scrollTo(0, start + delta * eased);
            if (i < steps) requestAnimationFrame(tick);
            else resolve();
          };
          requestAnimationFrame(tick);
        })""",
        {"y": y, "steps": steps},
    )
    page.wait_for_timeout(pause)


def section_y(page, sel):
    return page.evaluate(
        """(sel) => {
          const el = document.querySelector(sel);
          const top = el.getBoundingClientRect().top + window.scrollY;
          return Math.max(0, top - 80);
        }""",
        sel,
    )


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=str(VIDEO_DIR),
            record_video_size={"width": 1280, "height": 800},
        )
        page = context.new_page()
        page.goto(URL, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(1800)

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1200)

        # Demonstrate smooth anchor navigation
        page.locator('.nav-desktop a[href="#amenities"]').click()
        page.wait_for_timeout(1400)
        page.locator('.nav-desktop a[href="#gallery"]').click()
        page.wait_for_timeout(1400)
        page.locator('.header-cta').click()
        page.wait_for_timeout(1400)

        # Booking widget interaction
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
        page.wait_for_timeout(700)
        page.mouse.click(200, 120)
        page.wait_for_timeout(500)

        # Continuous smooth scroll through sections
        for sel in ["#rooms", "#amenities", "#gallery", "#location", "#trust", "#footer"]:
            y = section_y(page, sel)
            smooth_scroll_to(page, y, steps=36, pause=900)

        page.wait_for_timeout(800)

        # Mobile pass
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(700)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(800)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(1000)
        page.locator("#navClose").click()
        page.wait_for_timeout(500)
        smooth_scroll_to(page, section_y(page, "#booking"), steps=24, pause=700)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(900)
        page.mouse.click(40, 120)
        page.wait_for_timeout(400)
        smooth_scroll_to(page, section_y(page, "#rooms"), steps=28, pause=800)
        smooth_scroll_to(page, section_y(page, "#gallery"), steps=30, pause=900)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "hotel-madona-homepage-walkthrough.webm"
            Path(video_path).rename(dest)
            print(f"Video saved: {dest}")
        else:
            print("No video recorded")


if __name__ == "__main__":
    main()
