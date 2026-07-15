#!/usr/bin/env python3
"""Record walkthrough video of Kalna Ligzda prototype with smooth scrolling."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "kalna-walkthrough-raw"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def smooth_scroll(page, target_y, duration_ms=1800, steps=40):
    page.evaluate(
        """({ targetY, durationMs, steps }) => {
          return new Promise((resolve) => {
            const startY = window.scrollY;
            const delta = targetY - startY;
            const stepMs = durationMs / steps;
            let i = 0;
            function tick() {
              i += 1;
              const t = Math.min(1, i / steps);
              const eased = t < 0.5 ? 2*t*t : -1+(4-2*t)*t;
              window.scrollTo(0, startY + delta * eased);
              if (t < 1) setTimeout(tick, stepMs);
              else resolve();
            }
            tick();
          });
        }""",
        {"targetY": target_y, "durationMs": duration_ms, "steps": steps},
    )


def section_y(page, sel):
    return page.evaluate(
        f"() => {{ const el = document.querySelector('{sel}'); return el ? el.getBoundingClientRect().top + window.scrollY - 20 : 0; }}"
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

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1200)

        # Demonstrate smooth CSS scroll via nav anchors
        for href in ["#rooms", "#amenities", "#gallery"]:
            page.locator(f'.nav-desktop a[href="{href}"]').click()
            page.wait_for_timeout(1400)

        page.locator('.nav-desktop a[href="#booking"]').click()
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
        page.wait_for_timeout(600)
        page.locator("#adultsPlus").click()
        page.wait_for_timeout(400)
        page.locator("#childrenPlus").click()
        page.wait_for_timeout(500)
        page.mouse.click(200, 120)
        page.wait_for_timeout(400)

        # Continuous smooth scroll through remaining sections
        for sel in ["#rooms", "#amenities", "#gallery", "#location", "#trust", "#footer"]:
            y = section_y(page, sel)
            smooth_scroll(page, y, duration_ms=1600 if sel != "#footer" else 1200)
            page.wait_for_timeout(900)

        # Mobile viewport
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(700)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(800)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(1000)
        page.locator("#navClose").click()
        page.wait_for_timeout(500)
        smooth_scroll(page, section_y(page, "#booking"), duration_ms=1200)
        page.wait_for_timeout(600)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(900)
        page.mouse.click(40, 80)
        page.wait_for_timeout(400)
        smooth_scroll(page, section_y(page, "#rooms"), duration_ms=1400)
        page.wait_for_timeout(800)
        mid = page.evaluate("document.body.scrollHeight / 2")
        smooth_scroll(page, mid, duration_ms=1600)
        page.wait_for_timeout(1000)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "kalna-ligzda-prototype-walkthrough.webm"
            Path(video_path).rename(dest)
            print(f"Video saved: {dest}")
        else:
            print("No video recorded")


if __name__ == "__main__":
    main()
