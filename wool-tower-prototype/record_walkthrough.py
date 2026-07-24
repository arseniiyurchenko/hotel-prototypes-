#!/usr/bin/env python3
"""Record a smooth continuous walkthrough of the Wool Tower prototype."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/index.html?v=walk"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "wool-tower-walkthrough-frames"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def smooth_scroll(page, to_y: float, duration_ms: int = 1800):
    page.evaluate(
        """async ([toY, duration]) => {
          const startY = window.scrollY;
          const delta = toY - startY;
          if (Math.abs(delta) < 2) return;
          const start = performance.now();
          await new Promise((resolve) => {
            const step = (now) => {
              const t = Math.min(1, (now - start) / duration);
              const eased = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
              window.scrollTo(0, startY + delta * eased);
              if (t < 1) requestAnimationFrame(step);
              else resolve();
            };
            requestAnimationFrame(step);
          });
        }""",
        [to_y, duration_ms],
    )


def section_top(page, selector: str) -> float:
    return page.evaluate(
        """(sel) => {
          const el = document.querySelector(sel);
          const pad = parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) || 0;
          return Math.max(0, el.getBoundingClientRect().top + window.scrollY - pad);
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
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        page.goto(URL, wait_until="networkidle", timeout=120000)
        page.wait_for_timeout(2200)

        # Hero hold
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1800)

        # Continuous smooth scroll through page body
        height = page.evaluate("document.body.scrollHeight")
        viewport = 800
        y = 0
        while y < height - viewport:
            y = min(height - viewport, y + 520)
            smooth_scroll(page, y, 1400)
            page.wait_for_timeout(450)

        page.wait_for_timeout(700)
        smooth_scroll(page, 0, 1600)
        page.wait_for_timeout(900)

        # Demonstrate smooth anchor navigation via header/nav
        for href in ["#spaces", "#features", "#weddings", "#conferences", "#booking"]:
            if href == "#booking":
                page.locator(".header-cta").click()
            else:
                page.locator(f'.nav-desktop a[href="{href}"]').click()
            page.wait_for_timeout(1600)

        # Booking widget interactions
        page.wait_for_timeout(500)
        page.locator("#viewingDate").click()
        page.wait_for_timeout(350)
        page.locator("#viewingDate").fill("2026-09-15")
        page.wait_for_timeout(500)
        page.locator("#preferredSeason").select_option("autumn")
        page.wait_for_timeout(400)
        page.locator("#preferredYear").select_option("2027")
        page.wait_for_timeout(400)
        page.locator("#guestsPlus").click()
        page.wait_for_timeout(350)
        page.locator("#guestsPlus").click()
        page.wait_for_timeout(350)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(450)
        page.locator("#coupleNames").fill("Sam & Riley")
        page.wait_for_timeout(400)
        page.locator("#email").fill("hello@example.com")
        page.wait_for_timeout(350)
        page.locator("#viewingSubmit").click()
        page.wait_for_timeout(1200)

        # Smooth scroll back up a bit, then mobile
        smooth_scroll(page, section_top(page, "#weddings"), 1500)
        page.wait_for_timeout(800)

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(700)
        smooth_scroll(page, 0, 900)
        page.wait_for_timeout(900)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(1100)
        page.locator('#navMobile a[href="#booking"]').click()
        page.wait_for_timeout(1700)
        page.locator("#guestsMinus").click()
        page.wait_for_timeout(400)
        page.locator("#guestsPlus").click()
        page.wait_for_timeout(700)
        smooth_scroll(page, section_top(page, "#spaces"), 1400)
        page.wait_for_timeout(1000)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if not video_path:
            raise SystemExit("No video recorded")

        dest = ARTIFACTS / "wool-tower-prototype-walkthrough.webm"
        Path(video_path).replace(dest)
        print(f"Video saved: {dest} ({dest.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
