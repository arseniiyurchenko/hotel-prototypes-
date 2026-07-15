#!/usr/bin/env python3
"""Record a smooth continuous walkthrough of the VIGA prototype."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8770/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "viga-walkthrough-video"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def smooth_scroll_to(page, y, duration_ms=1400):
    page.evaluate(
        """({y, duration}) => new Promise(resolve => {
          const start = window.scrollY;
          const delta = y - start;
          if (Math.abs(delta) < 2) { resolve(); return; }
          const t0 = performance.now();
          function frame(now) {
            const t = Math.min(1, (now - t0) / duration);
            const eased = t < 0.5 ? 2*t*t : 1 - Math.pow(-2*t + 2, 2) / 2;
            window.scrollTo(0, start + delta * eased);
            if (t < 1) requestAnimationFrame(frame);
            else resolve();
          }
          requestAnimationFrame(frame);
        })""",
        {"y": y, "duration": duration_ms},
    )


def smooth_scroll_to_selector(page, sel, duration_ms=1400, offset=80):
    y = page.evaluate(
        """({sel, offset}) => {
          const el = document.querySelector(sel);
          return Math.max(0, el.getBoundingClientRect().top + window.scrollY - offset);
        }""",
        {"sel": sel, "offset": offset},
    )
    smooth_scroll_to(page, y, duration_ms)


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

        # Hero hold
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1600)

        # Smooth scroll down through hero into booking
        smooth_scroll_to_selector(page, "#booking", 1600)
        page.wait_for_timeout(700)

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
        page.wait_for_timeout(500)
        page.mouse.click(40, 120)
        page.wait_for_timeout(400)

        # Demonstrate smooth anchor navigation (not instant jump)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(800)
        page.locator('a.nav-desktop[href="#gallery"], .nav-desktop a[href="#gallery"]').first.click()
        page.wait_for_timeout(1600)

        page.locator('.nav-desktop a[href="#rooms"]').first.click()
        page.wait_for_timeout(1500)

        # Continuous smooth scroll through remaining sections
        for sel, dur in [
            ("#amenities", 1500),
            ("#gallery", 1600),
            ("#location", 1500),
            ("#trust", 1400),
            ("#footer", 1400),
        ]:
            smooth_scroll_to_selector(page, sel, dur)
            page.wait_for_timeout(900)

        # Slow continuous scroll back up a bit then to top
        mid = page.evaluate("() => document.body.scrollHeight * 0.35")
        smooth_scroll_to(page, mid, 1800)
        page.wait_for_timeout(500)
        smooth_scroll_to(page, 0, 1600)
        page.wait_for_timeout(700)

        # Mobile viewport
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(700)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(700)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(900)
        page.locator("#navClose").click()
        page.wait_for_timeout(500)
        smooth_scroll_to_selector(page, "#booking", 1200)
        page.wait_for_timeout(600)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(900)
        smooth_scroll_to_selector(page, "#rooms", 1400)
        page.wait_for_timeout(800)
        smooth_scroll_to_selector(page, "#gallery", 1500)
        page.wait_for_timeout(1000)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "viga-guesthouse-prototype-walkthrough.webm"
            Path(video_path).rename(dest)
            print(f"Video saved: {dest}")
        else:
            print("No video recorded")
            raise SystemExit(1)


if __name__ == "__main__":
    main()
