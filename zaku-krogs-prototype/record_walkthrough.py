#!/usr/bin/env python3
"""Record smooth walkthrough video of Zaķu krogs prototype."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "zaku-krogs-walkthrough-raw"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def smooth_scroll(page, target_y, duration_ms=1400):
    page.evaluate(
        """({ targetY, duration }) => {
          return new Promise((resolve) => {
            const startY = window.scrollY;
            const diff = targetY - startY;
            const start = performance.now();
            function step(now) {
              const t = Math.min(1, (now - start) / duration);
              const eased = t < 0.5 ? 2*t*t : -1 + (4 - 2*t)*t;
              window.scrollTo(0, startY + diff * eased);
              if (t < 1) requestAnimationFrame(step);
              else resolve();
            }
            requestAnimationFrame(step);
          });
        }""",
        {"targetY": target_y, "duration": duration_ms},
    )


def section_top(page, selector):
    return page.locator(selector).evaluate(
        "el => el.getBoundingClientRect().top + window.scrollY - 80"
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
        page.wait_for_timeout(2000)

        # Hero hold
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1600)

        # Smooth continuous scroll through page
        total = page.evaluate("document.body.scrollHeight - window.innerHeight")
        for y in range(0, int(total) + 1, 280):
            smooth_scroll(page, min(y, total), 700)
            page.wait_for_timeout(250)

        page.wait_for_timeout(800)

        # Demonstrate smooth anchor navigation
        page.evaluate("window.scrollTo({ top: 0, behavior: 'instant' })")
        page.wait_for_timeout(700)
        for href in ["#rooms", "#tavern", "#amenities", "#gallery", "#location"]:
            page.locator(f'.nav-desktop a[href="{href}"]').click()
            page.wait_for_timeout(1400)

        # Trust has no header nav link — smooth-scroll into view
        smooth_scroll(page, section_top(page, "#trust"), 1600)
        page.wait_for_timeout(1000)

        # Booking widget interaction
        page.locator('a[href="#booking"]').first.click()
        page.wait_for_timeout(1200)
        tomorrow = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+3); return d.toISOString().split('T')[0]; }"
        )
        checkout = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+6); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#checkin").fill(tomorrow)
        page.wait_for_timeout(500)
        page.locator("#checkout").fill(checkout)
        page.wait_for_timeout(500)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(600)
        page.locator("#adultsPlus").click()
        page.wait_for_timeout(350)
        page.locator("#childrenPlus").click()
        page.wait_for_timeout(500)
        page.mouse.click(200, 120)
        page.wait_for_timeout(400)
        page.locator("#searchBtn").click()
        page.wait_for_timeout(1200)

        # Mobile pass
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(700)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(800)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(900)
        page.locator('#navMobile a[href="#gallery"]').click()
        page.wait_for_timeout(1400)
        smooth_scroll(page, section_top(page, "#footer"), 1600)
        page.wait_for_timeout(1000)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "zaku-krogs-homepage-walkthrough.webm"
            Path(video_path).rename(dest)
            print(f"Video saved: {dest}")
        else:
            print("No video recorded")
            raise SystemExit(1)


if __name__ == "__main__":
    main()
