#!/usr/bin/env python3
"""Record a smooth continuous walkthrough of the Dzintarkrasts prototype."""
import os
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
URL = (ROOT / "index.html").as_uri()
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "dzintarkrasts-walkthrough-raw"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
OUT = ARTIFACTS / "dzintarkrasts-homepage-walkthrough.webm"


def smooth_scroll(page, to_y, duration_ms=1400):
    page.evaluate(
        """async ({ toY, duration }) => {
          const start = window.scrollY;
          const delta = toY - start;
          if (Math.abs(delta) < 2) return;
          const t0 = performance.now();
          await new Promise(resolve => {
            function frame(now) {
              const t = Math.min(1, (now - t0) / duration);
              const eased = 1 - Math.pow(1 - t, 3);
              window.scrollTo(0, start + delta * eased);
              if (t < 1) requestAnimationFrame(frame);
              else resolve();
            }
            requestAnimationFrame(frame);
          });
        }""",
        {"toY": to_y, "duration": duration_ms},
    )


def section_y(page, sel):
    return page.evaluate(
        """(sel) => {
          const el = document.querySelector(sel);
          const top = el.getBoundingClientRect().top + window.scrollY;
          return Math.max(0, top - 70);
        }""",
        sel,
    )


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(VIDEO_DIR),
            record_video_size={"width": 1280, "height": 720},
        )
        page = context.new_page()
        page.goto(URL, wait_until="networkidle", timeout=120000)
        page.wait_for_timeout(1800)

        # Hero hold
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1600)

        # Smooth nav to booking via CTA
        page.locator('.hero-actions a[href="#booking"]').click()
        page.wait_for_timeout(1600)

        # Booking widget interaction
        tomorrow = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+2); return d.toISOString().slice(0,10); }"
        )
        checkout = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+5); return d.toISOString().slice(0,10); }"
        )
        page.locator("#checkin").fill(tomorrow)
        page.wait_for_timeout(450)
        page.locator("#checkout").fill(checkout)
        page.wait_for_timeout(450)
        page.locator("#guestsDisplay").click()
        page.wait_for_timeout(500)
        page.locator('[data-target="adults"][data-action="increase"]').click()
        page.wait_for_timeout(350)
        page.locator('[data-target="children"][data-action="increase"]').click()
        page.wait_for_timeout(450)
        page.mouse.click(200, 120)
        page.wait_for_timeout(400)
        page.locator("#bookingForm button[type=submit]").click()
        page.wait_for_timeout(900)

        # Continuous smooth scroll through sections
        for sel in ["#rooms", "#amenities", "#gallery", "#location", "#trust", "#footer"]:
            y = section_y(page, sel)
            smooth_scroll(page, y, 1600)
            page.wait_for_timeout(900)

        # Demonstrate smooth nav from header
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(700)
        page.locator('.nav-desktop a[href="#gallery"]').click()
        page.wait_for_timeout(1700)
        page.locator('.nav-desktop a[href="#amenities"]').click()
        page.wait_for_timeout(1500)

        # Mobile pass
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(600)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(800)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(700)
        page.locator('#navMobile a[href="#rooms"]').click()
        page.wait_for_timeout(1400)
        smooth_scroll(page, section_y(page, "#booking"), 1200)
        page.wait_for_timeout(500)
        page.locator("#guestsDisplay").click()
        page.wait_for_timeout(900)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)

        video = page.video
        page.close()
        context.close()
        browser.close()

        if video:
            raw = Path(video.path())
            if raw.exists():
                subprocess.run(
                    [
                        "ffmpeg", "-y", "-i", str(raw),
                        "-c:v", "libvpx-vp9", "-b:v", "1.2M", "-an",
                        str(OUT),
                    ],
                    check=False,
                    capture_output=True,
                )
                if OUT.exists():
                    print(f"Video saved: {OUT}")
                else:
                    dest = ARTIFACTS / "dzintarkrasts-homepage-walkthrough-raw.webm"
                    raw.rename(dest)
                    print(f"ffmpeg failed; raw video: {dest}")
            else:
                print("No raw video path")
        else:
            print("No video recorded")


if __name__ == "__main__":
    main()
