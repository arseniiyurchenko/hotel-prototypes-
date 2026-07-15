#!/usr/bin/env python3
"""Record a smooth continuous walkthrough of the Rīteņi prototype."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8771/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "riiteni-walkthrough-raw"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def smooth_scroll_to(page, y, duration_ms=1200):
    page.evaluate(
        """({ y, duration }) => new Promise((resolve) => {
            const start = window.scrollY;
            const delta = y - start;
            const t0 = performance.now();
            function frame(now) {
                const t = Math.min(1, (now - t0) / duration);
                const eased = t < 0.5 ? 2*t*t : -1 + (4 - 2*t) * t;
                window.scrollTo(0, start + delta * eased);
                if (t < 1) requestAnimationFrame(frame);
                else resolve();
            }
            requestAnimationFrame(frame);
        })""",
        {"y": y, "duration": duration_ms},
    )


def section_top(page, sel):
    return page.evaluate(
        """(sel) => {
            const el = document.querySelector(sel);
            const top = el.getBoundingClientRect().top + window.scrollY;
            return Math.max(0, top - 72);
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
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(1800)

        # Start at hero
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1200)

        # Demonstrate smooth CSS anchor navigation
        for href in ["#booking", "#rooms", "#amenities"]:
            page.locator(f'.nav-desktop a[href="{href}"]').click()
            page.wait_for_timeout(1400)

        # Booking widget interaction
        smooth_scroll_to(page, section_top(page, "#booking"), 900)
        page.wait_for_timeout(500)
        page.locator("#checkin").fill("2026-07-20")
        page.wait_for_timeout(400)
        page.locator("#checkout").fill("2026-07-24")
        page.wait_for_timeout(400)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(500)
        page.locator("#adultsPlus").click()
        page.wait_for_timeout(350)
        page.locator("#childrenPlus").click()
        page.wait_for_timeout(350)
        page.locator("#roomType").select_option("cottage")
        page.wait_for_timeout(500)
        page.mouse.click(640, 120)
        page.wait_for_timeout(400)

        # Continuous smooth scroll through remaining sections
        for sel in ["#rooms", "#amenities", "#gallery", "#location", "#trust", "#footer"]:
            smooth_scroll_to(page, section_top(page, sel), 1400)
            page.wait_for_timeout(900)

        # Click CTA to demonstrate smooth return to booking
        page.locator(".header-cta").click()
        page.wait_for_timeout(1500)

        # Mobile viewport pass
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(700)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(800)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(900)
        page.locator('#navMobile a[href="#gallery"]').click()
        page.wait_for_timeout(1400)
        smooth_scroll_to(page, section_top(page, "#location"), 1200)
        page.wait_for_timeout(800)
        smooth_scroll_to(page, section_top(page, "#footer"), 1200)
        page.wait_for_timeout(1000)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "riiteni-guesthouse-prototype-walkthrough.webm"
            Path(video_path).rename(dest)
            print(f"Video saved: {dest}")
            print(f"Size: {dest.stat().st_size} bytes")
        else:
            print("No video recorded")
            raise SystemExit(1)


if __name__ == "__main__":
    main()
