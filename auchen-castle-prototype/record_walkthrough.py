#!/usr/bin/env python3
"""Record a smooth continuous walkthrough of the Auchen Castle prototype."""

from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8772/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "walkthrough-video-smooth"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def smooth_scroll_to(page, y, duration_ms=1600):
    page.evaluate(
        """({ targetY, duration }) => {
          return new Promise((resolve) => {
            if (window.__auchenStopScroll) window.__auchenStopScroll();
            const startY = window.scrollY;
            const delta = targetY - startY;
            if (Math.abs(delta) < 2) { resolve(); return; }
            const start = performance.now();
            let raf = 0;
            function frame(now) {
              const t = Math.min(1, (now - start) / duration);
              const eased = t < 0.5 ? 2*t*t : 1 - Math.pow(-2*t + 2, 2) / 2;
              window.scrollTo(0, startY + delta * eased);
              if (t < 1) raf = requestAnimationFrame(frame);
              else resolve();
            }
            raf = requestAnimationFrame(frame);
          });
        }""",
        {"targetY": int(y), "duration": duration_ms},
    )
    page.wait_for_timeout(100)


def section_top(page, sel):
    return page.evaluate(
        """(sel) => {
          const el = document.querySelector(sel);
          if (!el) return 0;
          const y = el.getBoundingClientRect().top + window.scrollY;
          const pad = parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) || 92;
          return Math.max(0, y - pad);
        }""",
        sel,
    )


def wait_for_near_section(page, section_id, timeout_ms=2500):
    page.wait_for_function(
        f"""() => {{
          const el = document.getElementById('{section_id}');
          if (!el) return false;
          const headerH = document.querySelector('.site-header').getBoundingClientRect().height;
          const top = el.getBoundingClientRect().top;
          return top >= headerH - 30 && top < headerH + 160;
        }}""",
        timeout=timeout_ms,
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
        # Expose stop helper used by recorder resets
        page.add_init_script(
            """
            window.__auchenStopScroll = window.__auchenStopScroll || function(){};
            """
        )
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(1600)
        # Patch stop helper to page's real canceller if present via noop; recorder uses local RAF
        page.evaluate("() => window.scrollTo(0, 0)")
        page.wait_for_timeout(900)

        # 1) Smooth continuous scroll: hero -> inquiry
        smooth_scroll_to(page, section_top(page, "#inquiry"), 1800)
        page.wait_for_timeout(500)

        # 2) Enquiry widget (date + selectors — event venue analogue of booking widget)
        event_date = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+21); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#eventDate").click()
        page.wait_for_timeout(400)
        page.locator("#eventDate").fill(event_date)
        page.wait_for_timeout(500)
        page.locator("#delegateBand").select_option(label="51 to 75")
        page.wait_for_timeout(500)
        page.locator("#eventType").select_option(label="Conference / meeting")
        page.wait_for_timeout(500)
        page.locator("#packageInterest").select_option(label="Day Delegate (£45 pp)")
        page.wait_for_timeout(550)
        page.locator("#inquiryForm button[type='submit']").click()
        page.wait_for_timeout(1000)

        # 3) Back to top, then demonstrate smooth nav anchors
        smooth_scroll_to(page, 0, 1400)
        page.wait_for_timeout(700)

        for href in ["#spaces", "#features", "#packages", "#gallery", "#location"]:
            page.locator(f'.nav-desktop a[href="{href}"]').click()
            wait_for_near_section(page, href[1:], timeout_ms=3000)
            page.wait_for_timeout(850)

        # 4) Continuous smooth scroll through contact / footer
        smooth_scroll_to(page, section_top(page, "#contact"), 2000)
        page.wait_for_timeout(800)
        max_y = page.evaluate("() => Math.max(0, document.body.scrollHeight - window.innerHeight)")
        smooth_scroll_to(page, max_y, 1500)
        page.wait_for_timeout(1000)

        # 5) Mobile viewport
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(700)
        page.evaluate("() => window.scrollTo(0, 0)")
        page.wait_for_timeout(800)

        page.locator("#menuToggle").click()
        page.wait_for_timeout(1000)
        page.locator('#navMobile a[href="#packages"]').click()
        wait_for_near_section(page, "packages", timeout_ms=3000)
        page.wait_for_timeout(900)

        # Smooth glide through remaining mobile sections
        for sel, dur in [("#gallery", 1800), ("#location", 1800), ("#contact", 2000)]:
            smooth_scroll_to(page, section_top(page, sel), dur)
            page.wait_for_timeout(700)

        context.close()
        browser.close()

    videos = sorted(VIDEO_DIR.glob("*.webm"), key=lambda p: p.stat().st_mtime)
    if not videos:
        raise SystemExit("No walkthrough video recorded")
    dest = ARTIFACTS / "auchen-castle-walkthrough.webm"
    if dest.exists():
        dest.unlink()
    videos[-1].replace(dest)
    print(f"Walkthrough saved to {dest} ({dest.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
