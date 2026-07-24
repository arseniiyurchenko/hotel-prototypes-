#!/usr/bin/env python3
"""Record a smooth continuous walkthrough of the Cavendish Banqueting prototype."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8771/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "cavendish-walkthrough-video"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def smooth_scroll_to(page, y: float, steps: int = 40, step_ms: int = 40):
    """Animate window scroll from current position to target y."""
    start = page.evaluate("window.scrollY")
    target = max(0, float(y))
    for i in range(1, steps + 1):
        t = i / steps
        # ease-in-out
        eased = 0.5 - 0.5 * __import__("math").cos(3.1415926535 * t)
        pos = start + (target - start) * eased
        page.evaluate(f"window.scrollTo(0, {pos})")
        page.wait_for_timeout(step_ms)


def smooth_scroll_by(page, delta: float, steps: int = 24, step_ms: int = 35):
    start = page.evaluate("window.scrollY")
    smooth_scroll_to(page, start + delta, steps=steps, step_ms=step_ms)


def section_top(page, selector: str) -> float:
    return page.evaluate(
        f"""() => {{
          const el = document.querySelector('{selector}');
          if (!el) return 0;
          const y = el.getBoundingClientRect().top + window.scrollY;
          const pad = parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) || 0;
          return Math.max(0, y - pad);
        }}"""
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
        page.wait_for_timeout(2500)

        # Hero dwell
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(2000)

        # Smooth scroll into inquiry / booking widget
        smooth_scroll_to(page, section_top(page, "#inquiry"), steps=36, step_ms=40)
        page.wait_for_timeout(800)

        # Interact with booking widget: date, guests, function, day
        tomorrow = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+21); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#eventDate").click()
        page.wait_for_timeout(400)
        page.locator("#eventDate").fill(tomorrow)
        page.wait_for_timeout(600)

        page.locator("#guestBand").click()
        page.wait_for_timeout(350)
        page.locator("#guestBand").select_option(label="300 to 350")
        page.wait_for_timeout(600)

        page.locator("#functionType").click()
        page.wait_for_timeout(350)
        page.locator("#functionType").select_option(label="Wedding & Reception")
        page.wait_for_timeout(600)

        page.locator("#dayBand").select_option(label="Fri – Sun")
        page.wait_for_timeout(500)
        page.locator("#inquiryForm button[type='submit']").click()
        page.wait_for_timeout(1400)

        # Demonstrate smooth CSS anchor navigation (nav clicks)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(900)

        for href in ["#hall", "#features", "#gallery", "#location"]:
            page.locator(f'.nav-desktop a[href="{href}"]').click()
            # Allow CSS smooth scroll to run (do not jump)
            page.wait_for_timeout(1600)

        # Continuous smooth scroll through remaining page (contact → footer)
        smooth_scroll_to(page, section_top(page, "#contact"), steps=48, step_ms=40)
        page.wait_for_timeout(1000)
        doc_h = page.evaluate("document.body.scrollHeight - window.innerHeight")
        smooth_scroll_to(page, doc_h, steps=36, step_ms=40)
        page.wait_for_timeout(1200)

        # Continuous upward skim back through gallery (smooth, not section jumps)
        smooth_scroll_to(page, section_top(page, "#gallery"), steps=50, step_ms=35)
        page.wait_for_timeout(900)

        # Mobile viewport — continuous scroll
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(700)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1000)

        page.locator("#menuToggle").click()
        page.wait_for_timeout(1100)
        # Smooth anchor via mobile nav
        page.locator('#navMobile a[href="#features"]').click()
        page.wait_for_timeout(1600)

        page.locator("#menuToggle").click()
        page.wait_for_timeout(700)
        page.locator('#navMobile a[href="#inquiry"]').click()
        page.wait_for_timeout(1400)

        # Guest selector on mobile
        page.locator("#guestBand").select_option(label="150 to 200")
        page.wait_for_timeout(700)

        # Smooth continuous scroll down mobile page
        mobile_h = page.evaluate("document.body.scrollHeight - window.innerHeight")
        smooth_scroll_to(page, mobile_h * 0.35, steps=40, step_ms=35)
        page.wait_for_timeout(600)
        smooth_scroll_to(page, mobile_h * 0.7, steps=40, step_ms=35)
        page.wait_for_timeout(600)
        smooth_scroll_to(page, mobile_h, steps=36, step_ms=35)
        page.wait_for_timeout(1200)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "cavendish-walkthrough.webm"
            if dest.exists():
                dest.unlink()
            Path(video_path).rename(dest)
            print(f"Walkthrough saved to {dest}")
            print(f"Size: {dest.stat().st_size} bytes")
        else:
            print("No video recorded.")


if __name__ == "__main__":
    main()
