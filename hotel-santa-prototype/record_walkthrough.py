#!/usr/bin/env python3
"""Record smooth walkthrough video of Hotel Santa prototype."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "hotel-santa-walkthrough-raw"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def smooth_scroll(page, y, steps=28, pause=40):
    page.evaluate(
        """({y, steps}) => new Promise(resolve => {
          const start = window.scrollY;
          const delta = y - start;
          let i = 0;
          function tick() {
            i++;
            const t = i / steps;
            const ease = t < 0.5 ? 2*t*t : -1+(4-2*t)*t;
            window.scrollTo(0, start + delta * ease);
            if (i < steps) requestAnimationFrame(tick);
            else resolve();
          }
          requestAnimationFrame(tick);
        })""",
        {"y": y, "steps": steps},
    )
    page.wait_for_timeout(pause * steps // 4)


def section_y(page, sel):
    return page.evaluate(
        f"() => {{ const el = document.querySelector('{sel}'); return el ? el.offsetTop - 70 : 0; }}"
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
        page.wait_for_timeout(1800)

        # Smooth continuous scroll through page
        total = page.evaluate("() => document.body.scrollHeight")
        for y in range(0, total, 280):
            smooth_scroll(page, y, steps=18, pause=30)
            page.wait_for_timeout(350)

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1000)

        # Demonstrate smooth anchor nav (CTA)
        page.click("a.header-cta")
        page.wait_for_timeout(1600)

        # Booking interaction
        tomorrow = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+2); return d.toISOString().split('T')[0]; }"
        )
        checkout = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+5); return d.toISOString().split('T')[0]; }"
        )
        page.fill("#checkin", tomorrow)
        page.wait_for_timeout(500)
        page.fill("#checkout", checkout)
        page.wait_for_timeout(500)
        page.click("#guestTrigger")
        page.wait_for_timeout(700)
        page.click("#adultsPlus")
        page.wait_for_timeout(400)
        page.click("#childrenPlus")
        page.wait_for_timeout(700)
        page.mouse.click(200, 120)
        page.wait_for_timeout(500)

        # Click each nav link with smooth scroll
        for href in ["#rooms", "#amenities", "#gallery", "#location", "#trust"]:
            page.click(f'.nav-desktop a[href="{href}"]')
            page.wait_for_timeout(1400)

        # Mobile pass
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(700)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(900)
        page.click("#menuToggle")
        page.wait_for_timeout(1000)
        page.click("#navClose")
        page.wait_for_timeout(600)
        smooth_scroll(page, section_y(page, "#booking"), steps=22)
        page.wait_for_timeout(700)
        page.click("#guestTrigger")
        page.wait_for_timeout(900)
        mid = page.evaluate("() => document.body.scrollHeight / 2")
        smooth_scroll(page, mid, steps=24)
        page.wait_for_timeout(1000)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "hotel-santa-prototype-walkthrough.webm"
            Path(video_path).rename(dest)
            print(f"Video saved: {dest}")
        else:
            print("No video recorded")
            raise SystemExit(1)


if __name__ == "__main__":
    main()
