#!/usr/bin/env python3
"""Record smooth walkthrough video of Arnicāni prototype."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "arnicani-walkthrough-raw"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def smooth_scroll(page, target_y, steps=40, pause_ms=40):
    page.evaluate(
        """({ targetY, steps }) => {
          return new Promise((resolve) => {
            const start = window.scrollY;
            const delta = targetY - start;
            let i = 0;
            function frame() {
              i += 1;
              const t = i / steps;
              const ease = t < 0.5 ? 2*t*t : -1 + (4 - 2*t) * t;
              window.scrollTo(0, start + delta * ease);
              if (i < steps) requestAnimationFrame(frame);
              else resolve();
            }
            requestAnimationFrame(frame);
          });
        }""",
        {"targetY": target_y, "steps": steps},
    )
    page.wait_for_timeout(steps * pause_ms // 4 + 200)


def section_y(page, sel):
    return page.evaluate(
        """(sel) => {
          const el = document.querySelector(sel);
          if (!el) return 0;
          const top = el.getBoundingClientRect().top + window.scrollY;
          return Math.max(0, top - 70);
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
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(2000)

        # Start at top
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1500)

        # Demonstrate smooth anchor nav: Rooms
        page.locator('.nav-desktop a[href="#rooms"]').click()
        page.wait_for_timeout(1400)

        # Back toward booking via CTA feel — scroll smoothly to booking
        smooth_scroll(page, section_y(page, "#booking"), steps=45)
        page.wait_for_timeout(600)

        # Booking widget interaction
        tomorrow = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+3); return d.toISOString().split('T')[0]; }"
        )
        checkout_day = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+6); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#checkin").fill(tomorrow)
        page.wait_for_timeout(450)
        page.locator("#checkout").fill(checkout_day)
        page.wait_for_timeout(450)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(700)
        page.locator("#adultsPlus").click()
        page.wait_for_timeout(350)
        page.locator("#childrenPlus").click()
        page.wait_for_timeout(500)
        page.mouse.click(200, 120)
        page.wait_for_timeout(400)

        # Continuous smooth scroll through remaining sections
        for sel in ["#rooms", "#amenities", "#gallery", "#location", "#trust", "#footer"]:
            smooth_scroll(page, section_y(page, sel), steps=50)
            page.wait_for_timeout(900)

        # Demo another smooth nav click from mid-page
        page.locator('.nav-desktop a[href="#gallery"]').click()
        page.wait_for_timeout(1300)
        page.locator(".header-inner a.logo").click()
        page.wait_for_timeout(1200)

        # Mobile viewport
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(700)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(800)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(1000)
        page.locator('#navMobile a[href="#amenities"]').click()
        page.wait_for_timeout(1400)
        smooth_scroll(page, section_y(page, "#gallery"), steps=40)
        page.wait_for_timeout(800)
        smooth_scroll(page, section_y(page, "#footer"), steps=40)
        page.wait_for_timeout(1000)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "arnicani-prototype-walkthrough.webm"
            Path(video_path).rename(dest)
            print(f"Video saved: {dest}")
        else:
            print("No video recorded")


if __name__ == "__main__":
    main()
