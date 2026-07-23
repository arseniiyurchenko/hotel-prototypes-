#!/usr/bin/env python3
"""Record a walkthrough video of the Hotel Talsi homepage prototype."""

from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8770/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "hotel-talsi-walkthrough-video"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def smooth_scroll_to(page, y, steps=28, pause_ms=40):
    page.evaluate(
        """({ y, steps }) => {
          return new Promise(resolve => {
            const start = window.scrollY;
            const diff = y - start;
            let i = 0;
            const tick = () => {
              i += 1;
              const t = i / steps;
              const ease = t < 0.5 ? 2*t*t : -1+(4-2*t)*t;
              window.scrollTo(0, start + diff * ease);
              if (i < steps) requestAnimationFrame(tick);
              else resolve();
            };
            requestAnimationFrame(tick);
          });
        }""",
        {"y": y, "steps": steps},
    )
    page.wait_for_timeout(pause_ms)


def section_y(page, selector):
    return page.evaluate(
        """(sel) => {
          const el = document.querySelector(sel);
          if (!el) return 0;
          const top = el.getBoundingClientRect().top + window.scrollY;
          return Math.max(0, top - 72);
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
        page.goto(URL, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(2200)

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1500)

        # Continuous scroll through page
        for sel in ["#booking", "#rooms", "#amenities", "#gallery", "#location", "#trust", "#footer"]:
            y = section_y(page, sel)
            smooth_scroll_to(page, y, steps=36, pause_ms=700)

        # Back to top, then demonstrate smooth anchor navigation
        smooth_scroll_to(page, 0, steps=30, pause_ms=800)
        page.locator('.nav-desktop a[href="#rooms"]').click()
        page.wait_for_timeout(1400)
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
        page.wait_for_timeout(600)
        page.locator("#adultsPlus").click()
        page.wait_for_timeout(400)
        page.locator("#childrenPlus").click()
        page.wait_for_timeout(500)
        page.mouse.click(400, 200)
        page.wait_for_timeout(600)

        # Continue scrolling rooms → footer smoothly
        for sel in ["#rooms", "#amenities", "#gallery", "#location", "#trust"]:
            y = section_y(page, sel)
            smooth_scroll_to(page, y, steps=32, pause_ms=900)

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1200)

        # Mobile viewport pass
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(800)
        smooth_scroll_to(page, 0, steps=20, pause_ms=700)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(1000)
        page.locator('#mobileNav a[href="#location"]').click()
        page.wait_for_timeout(1400)
        page.locator("#guestTrigger").scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(900)
        page.mouse.click(40, 120)
        page.wait_for_timeout(500)
        smooth_scroll_to(page, section_y(page, "#gallery"), steps=28, pause_ms=800)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1200)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "hotel-talsi-prototype-walkthrough.webm"
            Path(video_path).rename(dest)
            print(f"Video saved: {dest}")
        else:
            print("No video recorded")


if __name__ == "__main__":
    main()
