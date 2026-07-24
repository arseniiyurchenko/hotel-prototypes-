#!/usr/bin/env python3
"""Record walkthrough video of Villa Decius prototype (desktop + mobile)."""

from pathlib import Path
import shutil
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "villa-decjusza-video-raw"
if VIDEO_DIR.exists():
    shutil.rmtree(VIDEO_DIR)
VIDEO_DIR.mkdir(parents=True)


def smooth_scroll(page, y, steps=28, pause=40):
    page.evaluate(
        """({y, steps}) => new Promise(resolve => {
          const start = window.scrollY;
          const delta = y - start;
          let i = 0;
          const tick = () => {
            i += 1;
            const t = i / steps;
            const ease = t < 0.5 ? 2*t*t : -1 + (4 - 2*t)*t;
            window.scrollTo(0, start + delta * ease);
            if (i < steps) requestAnimationFrame(tick);
            else resolve();
          };
          requestAnimationFrame(tick);
        })""",
        {"y": y, "steps": steps},
    )
    page.wait_for_timeout(pause * steps // 10)


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

        # Hero hold
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1600)

        # Smooth continuous scroll through page
        total = page.evaluate("() => document.body.scrollHeight")
        for y in range(0, total, 420):
            smooth_scroll(page, y, steps=22, pause=30)
            page.wait_for_timeout(350)

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(800)

        # Demonstrate smooth anchor navigation
        for href in ["#enquiry", "#spaces", "#amenities", "#gallery", "#location", "#trust"]:
            page.click(f'.nav-desktop a[href="{href}"]')
            page.wait_for_timeout(1400)

        # Enquiry widget interaction
        page.click('.nav-desktop a[href="#enquiry"]')
        page.wait_for_timeout(900)
        tomorrow = page.evaluate(
            "() => { const d=new Date(); d.setDate(d.getDate()+3); return d.toISOString().slice(0,10); }"
        )
        page.fill("#eventDate", tomorrow)
        page.wait_for_timeout(500)
        page.select_option("#eventType", "conference")
        page.wait_for_timeout(500)
        page.select_option("#guestCount", "51-100")
        page.wait_for_timeout(500)
        page.click("button.enquiry-submit")
        page.wait_for_timeout(1200)

        # Mobile viewport demo
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(700)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(900)
        page.click("#menuToggle")
        page.wait_for_timeout(1000)
        page.click('#navMobile a[href="#spaces"]')
        page.wait_for_timeout(1400)

        mobile_total = page.evaluate("() => document.body.scrollHeight")
        for y in range(0, mobile_total, 380):
            smooth_scroll(page, y, steps=18, pause=25)
            page.wait_for_timeout(280)

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1000)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if not video_path:
            raise SystemExit("No video recorded")

        out = ARTIFACTS / "villa-decjusza-walkthrough.webm"
        shutil.move(video_path, out)
        print(f"Wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
