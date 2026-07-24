#!/usr/bin/env python3
"""Record a smooth continuous walkthrough of the Lingnerschloss prototype."""

from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8767/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "lingnerschloss-walkthrough-video"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def smooth_scroll(page, target_y: float, duration_ms: int = 1800) -> None:
    page.evaluate(
        """async ({ targetY, durationMs }) => {
          const startY = window.scrollY;
          const delta = targetY - startY;
          if (Math.abs(delta) < 2) return;
          const start = performance.now();
          await new Promise((resolve) => {
            const step = (now) => {
              const t = Math.min(1, (now - start) / durationMs);
              const eased = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
              window.scrollTo(0, startY + delta * eased);
              if (t < 1) requestAnimationFrame(step);
              else resolve();
            };
            requestAnimationFrame(step);
          });
        }""",
        {"targetY": target_y, "durationMs": duration_ms},
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
        page.wait_for_timeout(2000)

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1200)

        # Smooth anchor navigation demos
        for sel in [
            ".nav-desktop a[href='#welcome']",
            ".nav-desktop a[href='#spaces']",
            ".nav-desktop a[href='#weddings']",
            "a.nav-cta",
        ]:
            page.locator(sel).first.click()
            page.wait_for_timeout(1700)

        # Inquiry widget interaction
        page.locator("#name").fill("Alex Example")
        page.wait_for_timeout(350)
        page.locator("#email").fill("alex@example.com")
        page.wait_for_timeout(300)
        event_date = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+21); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#date").fill(event_date)
        page.wait_for_timeout(400)
        page.locator("#option").select_option(label="Meeting / conference")
        page.wait_for_timeout(450)
        page.locator("#request").fill("Interested in Sternensaal for a company reception.")
        page.wait_for_timeout(500)
        page.locator("#inquiryForm button[type=submit]").click()
        page.wait_for_timeout(1100)

        # Continuous smooth scroll through full page
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(800)
        total = page.evaluate("() => Math.max(0, document.body.scrollHeight - window.innerHeight)")
        for i in range(1, 9):
            smooth_scroll(page, total * (i / 8), duration_ms=1500)
            page.wait_for_timeout(280)

        # Mobile pass
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(700)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(800)
        page.locator("#menuToggle").click()
        page.wait_for_timeout(900)
        page.locator('#navMobile a[href="#spaces"]').click()
        page.wait_for_timeout(1600)
        mtotal = page.evaluate("() => Math.max(0, document.body.scrollHeight - window.innerHeight)")
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)
        for i in range(1, 6):
            smooth_scroll(page, mtotal * (i / 5), duration_ms=1300)
            page.wait_for_timeout(220)

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "lingnerschloss-walkthrough.webm"
            Path(video_path).replace(dest)
            print(f"Wrote {dest}")
        else:
            print("No video recorded")


if __name__ == "__main__":
    main()
