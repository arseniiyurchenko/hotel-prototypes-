#!/usr/bin/env python3
"""Record a smooth walkthrough video of the Villa Anna prototype."""

from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8770/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "villa-anna-walkthrough-video"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def smooth_scroll(page, y, steps=28, step_ms=40):
    page.evaluate(
        """({ targetY, steps }) => {
          return new Promise((resolve) => {
            const start = window.scrollY;
            const delta = targetY - start;
            let i = 0;
            const tick = () => {
              i += 1;
              const t = i / steps;
              const eased = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
              window.scrollTo(0, start + delta * eased);
              if (i < steps) requestAnimationFrame(tick);
              else resolve();
            };
            requestAnimationFrame(tick);
          });
        }""",
        {"targetY": y, "steps": steps},
    )
    page.wait_for_timeout(steps * step_ms // 2)


def section_y(page, sel):
    return page.evaluate(
        """(sel) => {
          const el = document.querySelector(sel);
          const top = el.getBoundingClientRect().top + window.scrollY;
          const header = document.querySelector('.site-header').offsetHeight || 76;
          return Math.max(0, top - header - 8);
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
        page.wait_for_timeout(2200)

        # Start at hero
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1600)

        # Demonstrate smooth anchor navigation (CSS scroll-behavior)
        for href in ["#booking", "#rooms", "#amenities"]:
            page.locator(f'.nav-desktop a[href="{href}"]').click()
            page.wait_for_timeout(1400)

        # Booking widget interaction
        page.locator("#booking").scroll_into_view_if_needed()
        page.wait_for_timeout(700)
        tomorrow = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+3); return d.toISOString().split('T')[0]; }"
        )
        checkout = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+6); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#checkin").fill(tomorrow)
        page.wait_for_timeout(450)
        page.locator("#checkout").fill(checkout)
        page.wait_for_timeout(450)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(600)
        page.locator("#adultsPlus").click()
        page.wait_for_timeout(350)
        page.locator("#childrenPlus").click()
        page.wait_for_timeout(350)
        page.locator("#roomType").select_option("luxury")
        page.wait_for_timeout(500)
        page.mouse.click(200, 120)
        page.wait_for_timeout(400)

        # Continuous smooth scroll through remaining sections
        for sel in ["#rooms", "#amenities", "#gallery", "#location", "#trust", "#contact"]:
            y = section_y(page, sel)
            smooth_scroll(page, y, steps=36)
            page.wait_for_timeout(900)

        # Back toward top smoothly, then mobile pass
        smooth_scroll(page, 0, steps=40)
        page.wait_for_timeout(800)

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(700)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(800)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(900)
        page.locator('#navMobile a[href="#gallery"]').click()
        page.wait_for_timeout(1400)
        page.locator("#booking").scroll_into_view_if_needed()
        page.wait_for_timeout(700)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(900)
        y = section_y(page, "#location")
        smooth_scroll(page, y, steps=30)
        page.wait_for_timeout(1000)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "villa-anna-prototype-walkthrough.webm"
            Path(video_path).rename(dest)
            print(f"Video saved: {dest}")
        else:
            print("No video recorded")


if __name__ == "__main__":
    main()
