#!/usr/bin/env python3
"""Visual verification + smooth continuous walkthrough for Lingnerschloss prototype."""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8767/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
VIDEO_DIR = ARTIFACTS / "lingnerschloss-visual-walkthrough-raw"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)

results: dict = {
    "images": [],
    "header_spacing": {},
    "smooth_nav": [],
    "inquiry_widget": [],
    "layout": [],
    "mobile": [],
    "errors": [],
}


def smooth_scroll(page, target_y: float, duration_ms: int = 1800) -> None:
    """Animate window scroll continuously (no section jumps)."""
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


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=str(VIDEO_DIR),
            record_video_size={"width": 1280, "height": 800},
        )
        page = context.new_page()
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(1800)
        page.evaluate("document.documentElement.style.scrollBehavior = 'auto'")

        # --- Images ---
        page.evaluate(
            """async () => {
              const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
              for (const img of document.images) {
                img.loading = 'eager';
                img.scrollIntoView({ block: 'center' });
                await sleep(120);
              }
              window.scrollTo(0, 0);
              await sleep(400);
            }"""
        )
        page.wait_for_timeout(2000)
        for img in page.locator("img").all():
            src = img.get_attribute("src") or ""
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            results["images"].append({"src": src[:100], "ok": ok})
            if not ok:
                results["errors"].append(f"Broken image: {src}")

        # --- Header spacing from corners ---
        metrics = page.evaluate(
            """() => {
              const header = document.getElementById('siteHeader');
              const logo = document.querySelector('.logo');
              const cta = document.querySelector('.nav-cta');
              const hr = header.getBoundingClientRect();
              const lr = logo.getBoundingClientRect();
              const cr = cta.getBoundingClientRect();
              return {
                logoLeft: lr.left,
                ctaRightGap: window.innerWidth - cr.right,
                logoTop: lr.top,
                headerHeight: hr.height,
              };
            }"""
        )
        results["header_spacing"] = metrics
        if metrics["logoLeft"] < 16:
            results["errors"].append(f"Logo too close to left edge: {metrics['logoLeft']}px")
        if metrics["ctaRightGap"] < 16:
            results["errors"].append(f"CTA too close to right edge: {metrics['ctaRightGap']}px")
        if metrics["logoTop"] < 8:
            results["errors"].append(f"Logo too close to top edge: {metrics['logoTop']}px")

        page.screenshot(path=str(ARTIFACTS / "lingnerschloss-verify-hero.png"))

        # --- Smooth nav anchors ---
        page.evaluate(
            """() => {
              document.getElementById('navMobile')?.classList.remove('open');
              const nm = document.getElementById('navMobile');
              if (nm) nm.hidden = true;
              document.body.style.overflow = '';
              window.scrollTo(0, 0);
            }"""
        )
        page.wait_for_timeout(800)
        for href, section_id in [
            (".nav-desktop a[href='#welcome']", "welcome"),
            (".nav-desktop a[href='#spaces']", "spaces"),
            (".nav-desktop a[href='#weddings']", "weddings"),
            (".nav-desktop a[href='#impressions']", "impressions"),
            ("a.nav-cta[href='#inquiry']", "inquiry"),
            (".nav-desktop a[href='#location']", "location"),
        ]:
            before = page.evaluate("() => window.scrollY")
            t0 = time.time()
            samples = []
            loc = page.locator(href).first
            loc.wait_for(state="visible", timeout=5000)
            loc.click(timeout=10000)
            # Sample scroll position during animation
            for _ in range(12):
                page.wait_for_timeout(80)
                samples.append(page.evaluate("() => window.scrollY"))
            page.wait_for_timeout(700)
            after = page.evaluate("() => window.scrollY")
            elapsed = time.time() - t0
            unique = len(set(int(s) for s in samples))
            in_view = page.evaluate(
                """(id) => {
                  const el = document.getElementById(id);
                  const r = el.getBoundingClientRect();
                  const header = document.getElementById('siteHeader').offsetHeight;
                  return r.top >= header - 8 && r.top < window.innerHeight * 0.55;
                }""",
                section_id,
            )
            entry = {
                "section": section_id,
                "before": before,
                "after": after,
                "elapsed_s": round(elapsed, 2),
                "intermediate_samples": unique,
                "section_in_view": in_view,
            }
            results["smooth_nav"].append(entry)
            if after == before and section_id != "top":
                results["errors"].append(f"Nav to #{section_id} did not scroll")
            if unique < 3 and abs(after - before) > 80:
                results["errors"].append(
                    f"Nav to #{section_id} looked like an instant jump (samples={unique})"
                )
            if not in_view:
                results["errors"].append(f"Section #{section_id} not properly in view after nav")
            page.wait_for_timeout(450)

        # --- Inquiry widget (date + option selector; venue has inquiry, not hotel booking) ---
        page.locator("#inquiry").scroll_into_view_if_needed()
        page.wait_for_timeout(600)
        tomorrow = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+14); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#name").fill("Visual Review Guest")
        page.locator("#phone").fill("+49 351 000000")
        page.locator("#email").fill("review@example.com")
        page.locator("#date").fill(tomorrow)
        page.wait_for_timeout(400)
        page.locator("#option").select_option(label="Wedding")
        page.wait_for_timeout(400)
        page.locator("#request").fill("Sternensaal inquiry for ~80 guests")
        page.wait_for_timeout(350)
        date_val = page.locator("#date").input_value()
        opt_val = page.locator("#option").input_value()
        results["inquiry_widget"].append({"date": date_val, "option": opt_val})
        if date_val != tomorrow:
            results["errors"].append("Date picker did not accept value")
        if opt_val != "Wedding":
            results["errors"].append("Option selector did not update")
        page.locator("#inquiryForm button[type=submit]").click()
        page.wait_for_timeout(500)
        if page.locator("#formSuccess.show").count() == 0:
            results["errors"].append("Inquiry success state missing")
        else:
            results["inquiry_widget"].append("submit_ok")
        page.screenshot(path=str(ARTIFACTS / "lingnerschloss-verify-inquiry.png"))

        # --- Continuous smooth full-page scroll (for video) ---
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(900)
        total = page.evaluate("() => document.body.scrollHeight - window.innerHeight")
        # Continuous pass down the page in overlapping smooth segments
        steps = 8
        for i in range(1, steps + 1):
            target = total * (i / steps)
            smooth_scroll(page, target, duration_ms=1600)
            page.wait_for_timeout(350)
            # Overlap / empty check sample
            overlapping = page.evaluate(
                """() => {
                  const titles = [...document.querySelectorAll('h1,h2,h3')];
                  for (const el of titles) {
                    const r = el.getBoundingClientRect();
                    if (r.width === 0 || r.height === 0) continue;
                    if (r.bottom < 0 || r.top > innerHeight) continue;
                    const style = getComputedStyle(el);
                    if (style.opacity === '0' && el.classList.contains('visible') === false) continue;
                    // crude: ensure text not clipped by zero-size parent
                    if (el.scrollHeight > 0 && el.clientHeight === 0) return el.textContent;
                  }
                  return null;
                }"""
            )
            if overlapping:
                results["errors"].append(f"Possible layout issue near: {overlapping}")
        results["layout"].append("continuous_scroll_complete")
        page.screenshot(path=str(ARTIFACTS / "lingnerschloss-verify-footer.png"))

        # Demo smooth anchor nav again near end of desktop pass
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(700)
        page.locator(".nav-desktop a[href='#spaces']").first.click()
        page.wait_for_timeout(1600)
        page.locator("a.nav-cta").first.click()
        page.wait_for_timeout(1600)

        # --- Mobile ---
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(700)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(700)
        page.screenshot(path=str(ARTIFACTS / "lingnerschloss-verify-mobile-hero.png"))

        mobile_header = page.evaluate(
            """() => {
              const logo = document.querySelector('.logo');
              const toggle = document.getElementById('menuToggle');
              const lr = logo.getBoundingClientRect();
              const tr = toggle.getBoundingClientRect();
              return {
                logoLeft: lr.left,
                toggleRightGap: window.innerWidth - tr.right,
                toggleVisible: getComputedStyle(toggle).display !== 'none',
              };
            }"""
        )
        results["mobile"].append(mobile_header)
        if mobile_header["logoLeft"] < 12:
            results["errors"].append(f"Mobile logo cramped: {mobile_header['logoLeft']}px")
        if mobile_header["toggleRightGap"] < 12:
            results["errors"].append(f"Mobile menu toggle cramped: {mobile_header['toggleRightGap']}px")

        page.locator("#menuToggle").click()
        page.wait_for_timeout(700)
        page.screenshot(path=str(ARTIFACTS / "lingnerschloss-verify-mobile-menu.png"))
        page.locator('#navMobile a[href="#spaces"]').click()
        page.wait_for_timeout(1600)
        page.screenshot(path=str(ARTIFACTS / "lingnerschloss-verify-mobile-spaces.png"))

        # Smooth continuous mobile scroll
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)
        mtotal = page.evaluate("() => document.body.scrollHeight - window.innerHeight")
        for i in range(1, 6):
            smooth_scroll(page, mtotal * (i / 5), duration_ms=1400)
            page.wait_for_timeout(250)
        results["mobile"].append("mobile_scroll_ok")
        page.screenshot(path=str(ARTIFACTS / "lingnerschloss-verify-mobile-footer.png"))

        video_path = page.video.path() if page.video else None
        context.close()
        browser.close()

        if video_path:
            dest = ARTIFACTS / "lingnerschloss-visual-walkthrough.webm"
            Path(video_path).replace(dest)
            results["video"] = str(dest)
            print(f"Wrote {dest}")
        else:
            results["errors"].append("No video recorded")

    out = ARTIFACTS / "lingnerschloss-visual-verify.json"
    out.write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    if results["errors"]:
        print("FAILED", file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
