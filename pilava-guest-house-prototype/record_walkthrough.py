#!/usr/bin/env python3
"""Record a smooth continuous walkthrough of the Pilava prototype."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "pilava-walkthrough-raw"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def smooth_scroll(page, target_y, duration_ms=1400):
    page.evaluate(
        """({ targetY, duration }) => {
          return new Promise((resolve) => {
            const startY = window.scrollY;
            const diff = targetY - startY;
            const start = performance.now();
            function frame(now) {
              const t = Math.min(1, (now - start) / duration);
              const eased = t < 0.5 ? 2*t*t : -1 + (4 - 2*t) * t;
              window.scrollTo(0, startY + diff * eased);
              if (t < 1) requestAnimationFrame(frame);
              else resolve();
            }
            requestAnimationFrame(frame);
          });
        }""",
        {"targetY": target_y, "duration": duration_ms},
    )


def section_y(page, selector):
    return page.evaluate(
        """(sel) => {
          const el = document.querySelector(sel);
          if (!el) return 0;
          const top = el.getBoundingClientRect().top + window.scrollY;
          return Math.max(0, top - 70);
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
        page.goto(URL, wait_until="networkidle", timeout=120000)
        page.wait_for_timeout(2200)

        # Hero hold
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1600)

        # Continuous scroll through page sections
        for sel in [
            "#booking",
            "#accommodation",
            "#amenities",
            "#gallery",
            "#location",
            "#trust",
            "#footer",
        ]:
            y = section_y(page, sel)
            smooth_scroll(page, y, 1600)
            page.wait_for_timeout(900)

        # Back to top, then demonstrate smooth anchor navigation
        smooth_scroll(page, 0, 1200)
        page.wait_for_timeout(700)

        for href in ["#accommodation", "#gallery", "#location", "#booking"]:
            page.locator(f'.nav-desktop a[href="{href}"]').click()
            page.wait_for_timeout(1400)

        # Booking widget interaction
        checkin = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+3); return d.toISOString().split('T')[0]; }"
        )
        checkout = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+6); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#checkin").fill(checkin)
        page.wait_for_timeout(450)
        page.locator("#checkout").fill(checkout)
        page.wait_for_timeout(450)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(700)
        page.locator("#adultsPlus").click()
        page.wait_for_timeout(400)
        page.locator("#childrenPlus").click()
        page.wait_for_timeout(500)
        page.locator("#searchBtn").click()
        page.wait_for_timeout(1200)
        page.mouse.click(200, 120)
        page.wait_for_timeout(500)

        # Mobile viewport pass
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(700)
        smooth_scroll(page, 0, 800)
        page.wait_for_timeout(700)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(1000)
        page.locator('#navMobile a[href="#amenities"]').click()
        page.wait_for_timeout(1400)
        y = section_y(page, "#gallery")
        smooth_scroll(page, y, 1400)
        page.wait_for_timeout(900)
        y = section_y(page, "#footer")
        smooth_scroll(page, y, 1400)
        page.wait_for_timeout(1000)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if not video_path:
            raise SystemExit("No video recorded")

        dest_webm = ARTIFACTS / "pilava-prototype-walkthrough.webm"
        Path(video_path).rename(dest_webm)

        # Also produce mp4 for easier review when possible
        dest_mp4 = ARTIFACTS / "pilava-prototype-walkthrough.mp4"
        import subprocess

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(dest_webm),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-an",
                str(dest_mp4),
            ],
            check=False,
            capture_output=True,
        )
        print(f"Video saved: {dest_webm}")
        if dest_mp4.exists():
            print(f"MP4 saved: {dest_mp4}")


if __name__ == "__main__":
    main()
