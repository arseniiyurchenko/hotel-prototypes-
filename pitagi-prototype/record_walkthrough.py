#!/usr/bin/env python3
"""Record a smooth continuous walkthrough of the Pītagi prototype."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8777/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "pitagi-walkthrough-video"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def smooth_scroll_to(page, y, steps=28, pause_ms=40):
    page.evaluate(
        """({ targetY, steps }) => {
          return new Promise((resolve) => {
            const start = window.scrollY;
            const delta = targetY - start;
            let i = 0;
            function frame() {
              i += 1;
              const t = i / steps;
              const eased = t < 0.5 ? 2*t*t : -1+(4-2*t)*t;
              window.scrollTo(0, start + delta * eased);
              if (i < steps) requestAnimationFrame(frame);
              else resolve();
            }
            requestAnimationFrame(frame);
          });
        }""",
        {"targetY": y, "steps": steps},
    )
    page.wait_for_timeout(steps * pause_ms // 2)


def section_y(page, selector):
    return page.evaluate(
        """(sel) => {
          const el = document.querySelector(sel);
          return el ? Math.max(0, el.getBoundingClientRect().top + window.scrollY - 70) : 0;
        }""",
        selector,
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
        page.wait_for_timeout(1400)

        # Demonstrate smooth anchor navigation via header nav
        page.locator('.nav-desktop a[href="#rooms"]').click()
        page.wait_for_timeout(1600)
        page.locator('.nav-desktop a[href="#amenities"]').click()
        page.wait_for_timeout(1400)
        page.locator('.nav-desktop a[href="#booking"]').click()
        page.wait_for_timeout(1400)

        # Booking widget interaction
        tomorrow = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+2); return d.toISOString().split('T')[0]; }"
        )
        checkout_day = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+5); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#checkin").fill(tomorrow)
        page.wait_for_timeout(450)
        page.locator("#checkout").fill(checkout_day)
        page.wait_for_timeout(450)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(500)
        page.locator("#adultsPlus").click()
        page.wait_for_timeout(350)
        page.locator("#childrenPlus").click()
        page.wait_for_timeout(350)
        page.locator("#roomType").select_option("2bedroom")
        page.wait_for_timeout(500)
        page.mouse.click(200, 120)
        page.wait_for_timeout(350)
        page.locator("#searchBtn").click()
        page.wait_for_timeout(900)

        # Continuous smooth scroll through remaining sections
        for sel in ["#rooms", "#amenities", "#gallery", "#location", "#trust", "#footer"]:
            y = section_y(page, sel)
            smooth_scroll_to(page, y, steps=32, pause_ms=36)
            page.wait_for_timeout(900)

        # Slow scroll back toward top a bit
        smooth_scroll_to(page, section_y(page, "#gallery"), steps=24, pause_ms=30)
        page.wait_for_timeout(700)

        # Mobile viewport
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(700)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(800)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(900)
        page.locator('#mobileNav a[href="#gallery"]').click()
        page.wait_for_timeout(1500)
        smooth_scroll_to(page, section_y(page, "#booking"), steps=28, pause_ms=35)
        page.wait_for_timeout(600)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(900)
        page.mouse.click(40, 100)
        page.wait_for_timeout(400)
        smooth_scroll_to(page, section_y(page, "#rooms"), steps=26, pause_ms=35)
        page.wait_for_timeout(1000)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "pitagi-prototype-walkthrough.webm"
            Path(video_path).rename(dest)
            print(f"Video saved: {dest}")
        else:
            print("No video recorded")


if __name__ == "__main__":
    main()
