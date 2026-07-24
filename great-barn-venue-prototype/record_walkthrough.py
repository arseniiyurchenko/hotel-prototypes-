#!/usr/bin/env python3
"""Record a smooth continuous walkthrough of The Great Barn prototype."""

from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8772/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "great-barn-walkthrough-raw"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def smooth_scroll_to(page, y: float, duration_ms: int = 1600):
    page.evaluate(
        """async ({ y, duration }) => {
          document.documentElement.style.scrollBehavior = 'auto';
          const start = window.scrollY;
          const dist = y - start;
          if (Math.abs(dist) < 2) {
            document.documentElement.style.scrollBehavior = '';
            return;
          }
          const t0 = performance.now();
          await new Promise((resolve) => {
            const frame = (now) => {
              const t = Math.min(1, (now - t0) / duration);
              const eased = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
              window.scrollTo(0, start + dist * eased);
              if (t < 1) requestAnimationFrame(frame);
              else {
                document.documentElement.style.scrollBehavior = '';
                resolve();
              }
            };
            requestAnimationFrame(frame);
          });
        }""",
        {"y": y, "duration": duration_ms},
    )


def section_y(page, selector: str) -> float:
    return page.evaluate(
        """(sel) => {
          const el = document.querySelector(sel);
          const top = el.getBoundingClientRect().top + window.scrollY;
          const pad = parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) || 0;
          return Math.max(0, top - pad);
        }""",
        selector,
    )


def continuous_scroll(page, end_y: float, px_per_frame: float = 18):
    """Scroll steadily downward so the video shows continuous motion."""
    page.evaluate(
        """async ({ endY, step }) => {
          document.documentElement.style.scrollBehavior = 'auto';
          let y = window.scrollY;
          while (y < endY - 2) {
            y = Math.min(endY, y + step);
            window.scrollTo(0, y);
            await new Promise((r) => requestAnimationFrame(r));
          }
          window.scrollTo(0, endY);
          document.documentElement.style.scrollBehavior = '';
        }""",
        {"endY": end_y, "step": px_per_frame},
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
        page.evaluate("window.scrollTo({ top: 0, behavior: 'instant' })")
        page.wait_for_timeout(1200)

        # Demonstrate CSS smooth anchor navigation (user-click path)
        for href in ["#spaces", "#included", "#pricing", "#location", "#enquire"]:
            page.locator(f'.nav-desktop a[href="{href}"]').click()
            page.wait_for_timeout(1400)

        page.evaluate("window.scrollTo({ top: 0, behavior: 'instant' })")
        page.wait_for_timeout(900)

        # Continuous scroll through the full page
        full_height = page.evaluate("() => document.body.scrollHeight - window.innerHeight")
        continuous_scroll(page, full_height * 0.22, px_per_frame=14)
        page.wait_for_timeout(500)
        continuous_scroll(page, full_height * 0.48, px_per_frame=14)
        page.wait_for_timeout(500)
        continuous_scroll(page, full_height * 0.72, px_per_frame=14)
        page.wait_for_timeout(500)
        continuous_scroll(page, full_height, px_per_frame=14)
        page.wait_for_timeout(700)

        # Enquiry widget: date pickers + guest selector
        smooth_scroll_to(page, section_y(page, "#enquire"), 1200)
        page.wait_for_timeout(600)
        page.locator("#name").fill("Alex Morgan")
        page.wait_for_timeout(350)
        page.locator("#email").fill("alex@example.com")
        page.wait_for_timeout(350)

        event_day = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+45); return d.toISOString().slice(0,10); }"
        )
        view_day = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+12); return d.toISOString().slice(0,10); }"
        )
        page.locator("#eventDate").fill(event_day)
        page.wait_for_timeout(500)
        page.locator("#viewingDate").fill(view_day)
        page.wait_for_timeout(500)
        page.locator("#eventType").select_option("wedding")
        page.wait_for_timeout(400)

        page.locator("#guestTrigger").click()
        page.wait_for_timeout(700)
        page.locator("#ceremonyPlus").click()
        page.wait_for_timeout(400)
        page.locator("#ceremonyPlus").click()
        page.wait_for_timeout(400)
        page.locator("#eveningPlus").click()
        page.wait_for_timeout(500)
        page.locator("#message").fill("Looking at a Saturday hire with ceremony and evening reception")
        page.wait_for_timeout(500)
        page.mouse.click(40, 120)
        page.wait_for_timeout(400)
        page.locator("#submitEnquiry").click()
        page.wait_for_timeout(1200)

        # Mobile pass
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(800)
        page.evaluate("window.scrollTo({ top: 0, behavior: 'instant' })")
        page.wait_for_timeout(900)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(1100)
        page.locator('#navMobile a[href="#pricing"]').click()
        page.wait_for_timeout(1400)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(700)
        page.locator('#navMobile a[href="#enquire"]').click()
        page.wait_for_timeout(1200)
        page.locator("#guestTrigger").click()
        page.wait_for_timeout(900)
        mobile_end = page.evaluate("() => document.body.scrollHeight - window.innerHeight")
        continuous_scroll(page, mobile_end, px_per_frame=16)
        page.wait_for_timeout(1000)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "great-barn-venue-prototype-walkthrough.webm"
            Path(video_path).rename(dest)
            print(f"Video saved: {dest}")
        else:
            print("No video recorded")


if __name__ == "__main__":
    main()
