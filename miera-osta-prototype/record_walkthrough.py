#!/usr/bin/env python3
"""Record a smooth walkthrough video of the Miera Osta prototype."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8770/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "miera-osta-walkthrough-video"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def smooth_scroll_to(page, y, steps=28, pause_ms=35):
    page.evaluate(
        """({target, steps}) => {
          return new Promise((resolve) => {
            const start = window.scrollY;
            const delta = target - start;
            let i = 0;
            const tick = () => {
              i += 1;
              const t = i / steps;
              const eased = t < 0.5 ? 2*t*t : -1 + (4 - 2*t)*t;
              window.scrollTo(0, start + delta * eased);
              if (i < steps) requestAnimationFrame(tick);
              else resolve();
            };
            requestAnimationFrame(tick);
          });
        }""",
        {"target": y, "steps": steps},
    )
    page.wait_for_timeout(pause_ms * 2)


def section_y(page, sel):
    return page.evaluate(
        f"() => {{ const el = document.querySelector('{sel}'); return el ? el.getBoundingClientRect().top + window.scrollY - 70 : 0; }}"
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

        # Start at top
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1200)

        # Smooth continuous scroll through hero into booking
        smooth_scroll_to(page, section_y(page, "#booking"), steps=36, pause_ms=40)
        page.wait_for_timeout(800)

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
        page.locator("#roomType").select_option("romantic")
        page.wait_for_timeout(500)
        page.mouse.click(200, 160)
        page.wait_for_timeout(400)

        # Demonstrate smooth CSS anchor navigation (not jump)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(700)
        page.locator('.nav-desktop a[href="#rooms"]').click()
        page.wait_for_timeout(1400)
        page.locator('.nav-desktop a[href="#amenities"]').click()
        page.wait_for_timeout(1400)
        page.locator('.nav-desktop a[href="#gallery"]').click()
        page.wait_for_timeout(1400)

        # Continuous scroll through remaining sections
        for sel in ["#location", "#trust", "#footer"]:
            smooth_scroll_to(page, section_y(page, sel), steps=32, pause_ms=40)
            page.wait_for_timeout(900)

        # Mobile viewport
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(700)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(700)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(900)
        page.locator('#navMobile').get_by_role("link", name="Rezervācija").click()
        page.wait_for_timeout(1200)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(900)
        page.mouse.click(40, 120)
        page.wait_for_timeout(400)
        smooth_scroll_to(page, section_y(page, "#rooms"), steps=30, pause_ms=35)
        page.wait_for_timeout(800)
        smooth_scroll_to(page, section_y(page, "#gallery"), steps=30, pause_ms=35)
        page.wait_for_timeout(1000)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "miera-osta-prototype-walkthrough.webm"
            Path(video_path).rename(dest)
            print(f"Video saved: {dest}")
        else:
            print("No video recorded")


if __name__ == "__main__":
    main()
