#!/usr/bin/env python3
"""Record a smooth walkthrough video of the Četri Vēji prototype."""

from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8771/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "cetriveji-walkthrough-video"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def smooth_scroll_to(page, y_target, steps=28, step_delay=45):
    page.evaluate(
        """({ yTarget, steps }) => {
          return new Promise((resolve) => {
            const start = window.scrollY;
            const delta = yTarget - start;
            let i = 0;
            function frame() {
              i += 1;
              const t = i / steps;
              const eased = t < 0.5 ? 2*t*t : 1 - Math.pow(-2*t + 2, 2) / 2;
              window.scrollTo(0, start + delta * eased);
              if (i < steps) requestAnimationFrame(frame);
              else resolve();
            }
            requestAnimationFrame(frame);
          });
        }""",
        {"yTarget": y_target, "steps": steps},
    )
    page.wait_for_timeout(step_delay * 2)


def section_y(page, sel):
    return page.evaluate(
        """(sel) => {
          const el = document.querySelector(sel);
          if (!el) return 0;
          const rect = el.getBoundingClientRect();
          return Math.max(0, window.scrollY + rect.top - 70);
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
        page.wait_for_timeout(2200)

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1600)

        # Demonstrate smooth CSS anchor navigation
        page.locator('.nav-desktop a[href="#rooms"]').click()
        page.wait_for_timeout(1400)
        page.locator('.nav-desktop a[href="#amenities"]').click()
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
        page.wait_for_timeout(450)
        page.locator("#checkout").fill(checkout_day)
        page.wait_for_timeout(450)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(600)
        page.locator("#adultsPlus").click()
        page.wait_for_timeout(350)
        page.locator("#childrenPlus").click()
        page.wait_for_timeout(350)
        page.locator("#roomType").select_option("majas")
        page.wait_for_timeout(500)
        page.mouse.click(400, 180)
        page.wait_for_timeout(400)

        # Continuous smooth scroll through sections
        for sel in ["#rooms", "#amenities", "#gallery", "#location", "#trust", "#footer"]:
            y = section_y(page, sel)
            smooth_scroll_to(page, y, steps=36)
            page.wait_for_timeout(1100)

        page.wait_for_timeout(800)

        # Mobile pass
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(700)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(900)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(1000)
        page.locator('#navMobile a[href="#gallery"]').click()
        page.wait_for_timeout(1400)
        page.locator("#guestTrigger").scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(900)
        page.mouse.click(40, 120)
        page.wait_for_timeout(400)
        y_end = page.evaluate("() => document.body.scrollHeight")
        smooth_scroll_to(page, max(0, y_end - 900), steps=40)
        page.wait_for_timeout(1200)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "cetriveji-prototype-walkthrough.webm"
            Path(video_path).rename(dest)
            print(f"Video saved: {dest}")
        else:
            print("No video recorded")


if __name__ == "__main__":
    main()
