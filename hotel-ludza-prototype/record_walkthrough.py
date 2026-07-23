#!/usr/bin/env python3
"""Record smooth walkthrough video of Hotel Ludza prototype."""

import math
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "hotel-ludza-walkthrough-raw"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def smooth_scroll(page, target_y, duration_ms=1800):
    page.evaluate(
        """({ targetY, duration }) => {
          return new Promise((resolve) => {
            const startY = window.scrollY;
            const diff = targetY - startY;
            const start = performance.now();
            function step(now) {
              const t = Math.min(1, (now - start) / duration);
              const eased = t < 0.5 ? 2*t*t : -1+(4-2*t)*t;
              window.scrollTo(0, startY + diff * eased);
              if (t < 1) requestAnimationFrame(step);
              else resolve();
            }
            requestAnimationFrame(step);
          });
        }""",
        {"targetY": target_y, "duration": duration_ms},
    )


def section_top(page, sel):
    return page.evaluate(
        """(sel) => {
          const el = document.querySelector(sel);
          const y = el.getBoundingClientRect().top + window.scrollY;
          return Math.max(0, y - 72);
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
        page.goto(URL, wait_until="networkidle", timeout=120000)
        page.wait_for_timeout(2000)

        # Start at hero
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1500)

        # Demonstrate smooth anchor nav (CSS scroll-behavior)
        for href in ["#booking", "#rooms", "#amenities", "#gallery", "#location", "#trust"]:
            page.locator(f'.nav-desktop a[href="{href}"]').click()
            page.wait_for_timeout(1400)

        # Back to booking via header CTA
        page.locator('.header-cta a[href="#booking"]').click()
        page.wait_for_timeout(1200)

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
        page.wait_for_timeout(500)
        page.locator("#searchBtn").click()
        page.wait_for_timeout(1000)
        page.mouse.click(200, 120)
        page.wait_for_timeout(400)

        # Continuous smooth scroll through remaining page
        for sel in ["#rooms", "#amenities", "#gallery", "#location", "#trust", "#footer"]:
            y = section_top(page, sel)
            smooth_scroll(page, y, 2000)
            page.wait_for_timeout(900)

        # Mobile viewport
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(800)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1000)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(1000)
        page.locator('#navMobile a[href="#rooms"]').click()
        page.wait_for_timeout(1400)
        smooth_scroll(page, section_top(page, "#gallery"), 1800)
        page.wait_for_timeout(800)
        smooth_scroll(page, section_top(page, "#footer"), 1800)
        page.wait_for_timeout(1200)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "hotel-ludza-prototype-walkthrough.webm"
            Path(video_path).rename(dest)
            print(f"Video saved: {dest}")
        else:
            print("No video recorded")


if __name__ == "__main__":
    main()
