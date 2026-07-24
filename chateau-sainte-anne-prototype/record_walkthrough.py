#!/usr/bin/env python3
"""Visual verification + smooth continuous walkthrough video for Château Sainte-Anne prototype."""

from __future__ import annotations

import http.server
import json
import math
import threading
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
PORT = 8777
VIDEO_PATH = ARTIFACTS / "chateau-sainte-anne-walkthrough.webm"

results: dict = {
    "images": [],
    "header": {},
    "anchors": [],
    "widget": [],
    "layout": [],
    "mobile": [],
    "errors": [],
}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, format, *args):  # noqa: A003
        pass


def smooth_scroll(page, target_y: float, duration_ms: int = 1800) -> None:
    """Animate window scrollY continuously (easing) for the walkthrough video."""
    page.evaluate(
        """async ({ targetY, duration }) => {
          const startY = window.scrollY;
          const delta = targetY - startY;
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
        {"targetY": target_y, "duration": duration_ms},
    )
    page.wait_for_timeout(200)


def section_top(page, selector: str) -> float:
    return page.locator(selector).evaluate(
        "el => el.getBoundingClientRect().top + window.scrollY"
    )


def main() -> int:
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{PORT}/index.html"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                record_video_dir=str(ARTIFACTS),
                record_video_size={"width": 1280, "height": 720},
            )
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=120000)
            page.wait_for_timeout(1200)

            # --- Images ---
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1200)
            page.evaluate(
                """async () => {
                  const imgs = [...document.images];
                  await Promise.all(imgs.map(img =>
                    img.complete ? Promise.resolve() : new Promise(res => {
                      img.addEventListener('load', res, { once: true });
                      img.addEventListener('error', res, { once: true });
                    })
                  ));
                }"""
            )
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_function("() => window.scrollY < 2")
            page.wait_for_timeout(500)

            for img in page.locator("img").all():
                src = img.get_attribute("src") or ""
                ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
                results["images"].append({"src": src[:120], "ok": ok})
                if not ok:
                    results["errors"].append(f"Broken image: {src}")

            # --- Header spacing ---
            metrics = page.evaluate(
                """() => {
                  const brand = document.querySelector('.brand');
                  const cta = document.querySelector('.header-cta');
                  const toggle = document.getElementById('menuToggle');
                  const br = brand.getBoundingClientRect();
                  const cr = cta.getBoundingClientRect();
                  const tr = toggle.getBoundingClientRect();
                  const vw = window.innerWidth;
                  return {
                    brandLeft: br.left,
                    ctaRight: vw - cr.right,
                    toggleRight: vw - tr.right,
                    brandTop: br.top,
                    scrollY: window.scrollY,
                    headerPaddingInline: getComputedStyle(document.getElementById('siteHeader')).paddingLeft,
                  };
                }"""
            )
            results["header"] = metrics
            if metrics["brandLeft"] < 20:
                results["errors"].append(f"Logo too close to left edge: {metrics['brandLeft']:.1f}px")
            if metrics["ctaRight"] < 20:
                results["errors"].append(f"CTA too close to right edge: {metrics['ctaRight']:.1f}px")

            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_function("() => window.scrollY < 2")
            page.wait_for_timeout(300)
            page.screenshot(path=str(ARTIFACTS / "chateau-sainte-anne-desktop-hero.png"))
            hero_brand_visible = page.locator(".hero-brand").evaluate(
                "el => { const r = el.getBoundingClientRect(); return r.top >= 0 && r.bottom <= window.innerHeight; }"
            )
            results["header"]["heroBrandInView"] = hero_brand_visible
            if not hero_brand_visible:
                results["errors"].append("Hero brand not in viewport for hero screenshot")

            # --- Smooth anchor navigation (CSS scroll-behavior) ---
            anchors = [
                ("#espaces", '.nav-desktop a[href="#espaces"]'),
                ("#atouts", '.nav-desktop a[href="#atouts"]'),
                ("#tarifs", '.nav-desktop a[href="#tarifs"]'),
                ("#galerie", '.nav-desktop a[href="#galerie"]'),
                ("#acces", '.nav-desktop a[href="#acces"]'),
                ("#contact", "a.header-cta"),
            ]
            for href, click_sel in anchors:
                before = page.evaluate("() => window.scrollY")
                t0 = time.time()
                page.locator(click_sel).first.click()
                # Poll until near target — should take >150ms if smooth
                target = section_top(page, href)
                settled = False
                samples = []
                for _ in range(40):
                    page.wait_for_timeout(50)
                    y = page.evaluate("() => window.scrollY")
                    samples.append(y)
                    if abs(y - (target - 80)) < 120 or abs(y - target) < 160:
                        if len(samples) >= 3:
                            settled = True
                            break
                elapsed = (time.time() - t0) * 1000
                distinct = len({round(s, -1) for s in samples})
                smoothish = elapsed >= 180 or distinct >= 3
                results["anchors"].append(
                    {
                        "href": href,
                        "elapsed_ms": round(elapsed),
                        "distinct_samples": distinct,
                        "smooth": smoothish,
                        "final_y": samples[-1] if samples else None,
                    }
                )
                if not smoothish:
                    results["errors"].append(f"Anchor {href} appeared to jump instantly ({elapsed:.0f}ms)")
                if not settled and samples:
                    if abs(samples[-1] - before) < 50:
                        results["errors"].append(f"Anchor {href} did not scroll")
                page.wait_for_timeout(400)

            # Back to top smoothly for continuous page pass
            smooth_scroll(page, 0, 1400)
            page.wait_for_timeout(400)

            # --- Continuous smooth scroll through full page ---
            total_h = page.evaluate("() => document.body.scrollHeight - window.innerHeight")
            waypoints = [0.0]
            for sel in ["#presentation", "#espaces", "#atouts", "#tarifs", "#galerie", "#acces", "#contact"]:
                waypoints.append(section_top(page, sel) - 40)
            waypoints.append(float(total_h))
            for i in range(len(waypoints) - 1):
                dist = abs(waypoints[i + 1] - waypoints[i])
                dur = max(1200, min(2800, int(dist * 1.1)))
                smooth_scroll(page, waypoints[i + 1], dur)
                page.wait_for_timeout(350)

            # Layout checks at bottom
            overlaps = page.evaluate(
                """() => {
                  const issues = [];
                  const sections = [...document.querySelectorAll('section, .enquiry, footer')];
                  for (const el of sections) {
                    const r = el.getBoundingClientRect();
                    if (r.height < 8) issues.push('empty/collapsed: ' + (el.id || el.className));
                  }
                  const texts = [...document.querySelectorAll('h1,h2,h3,p')];
                  for (const el of texts) {
                    const style = getComputedStyle(el);
                    if (style.opacity === '0' && el.classList.contains('reveal') && !el.classList.contains('in')) {
                      // not yet revealed — ok if offscreen
                      continue;
                    }
                    if (el.scrollWidth > el.clientWidth + 2 && style.overflow === 'hidden') {
                      issues.push('possible text clip: ' + el.tagName + ' ' + (el.textContent || '').slice(0, 40));
                    }
                  }
                  return issues;
                }"""
            )
            results["layout"] = overlaps
            for issue in overlaps:
                if issue.startswith("empty"):
                    results["errors"].append(issue)

            page.screenshot(
                path=str(ARTIFACTS / "chateau-sainte-anne-desktop-full.png"),
                full_page=True,
            )

            # --- Enquiry widget: date pickers + guest selector ---
            page.locator("#contact").scroll_into_view_if_needed()
            page.wait_for_timeout(500)
            page.locator("#name").fill("Camille Dupont")
            page.locator("#email").fill("camille@example.com")
            page.locator("#eventDate").fill("2026-09-12")
            page.wait_for_timeout(400)
            page.locator("#altDate").fill("2026-09-19")
            page.wait_for_timeout(400)
            page.locator("#eventType").select_option("mariage")
            before_guests = page.locator("#guestsDisplay").input_value()
            page.locator("#guestsIncrease").click()
            page.wait_for_timeout(250)
            page.locator("#guestsIncrease").click()
            page.wait_for_timeout(250)
            page.locator("#guestsDecrease").click()
            page.wait_for_timeout(250)
            after_guests = page.locator("#guestsDisplay").input_value()
            results["widget"].append(f"guests before={before_guests!r} after={after_guests!r}")
            if before_guests == after_guests:
                results["errors"].append("Guest selector did not change count")
            page.locator("#message").fill("Grand Hall — cocktail puis dîner.")
            page.locator("#submitEnquiry").click()
            page.wait_for_timeout(400)
            status = page.locator("#formStatus").inner_text()
            results["widget"].append(f"form status: {status[:120]}")
            if "prototype" not in status.lower() and "Nathalie" not in status:
                results["errors"].append(f"Unexpected form status: {status}")
            page.screenshot(path=str(ARTIFACTS / "chateau-sainte-anne-desktop-contact.png"))

            # Demonstrate another smooth nav jump for the video
            smooth_scroll(page, 0, 1200)
            page.wait_for_timeout(300)
            page.locator('.nav-desktop a[href="#espaces"]').click()
            page.wait_for_timeout(1400)
            page.locator("a.header-cta").first.click()
            page.wait_for_timeout(1400)

            # --- Mobile ---
            page.set_viewport_size({"width": 390, "height": 844})
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(600)
            mob = page.evaluate(
                """() => {
                  const brand = document.querySelector('.brand');
                  const toggle = document.getElementById('menuToggle');
                  const br = brand.getBoundingClientRect();
                  const tr = toggle.getBoundingClientRect();
                  const vw = window.innerWidth;
                  return {
                    brandLeft: br.left,
                    toggleRight: vw - tr.right,
                    overflowX: document.documentElement.scrollWidth > window.innerWidth + 2,
                  };
                }"""
            )
            results["mobile"].append(mob)
            if mob["brandLeft"] < 16:
                results["errors"].append(f"Mobile logo cramped: {mob['brandLeft']:.1f}px")
            if mob["toggleRight"] < 16:
                results["errors"].append(f"Mobile menu toggle cramped: {mob['toggleRight']:.1f}px")
            if mob["overflowX"]:
                results["errors"].append("Horizontal overflow on mobile")

            page.locator("#menuToggle").click()
            page.wait_for_selector("#navMobile.open")
            page.wait_for_timeout(500)
            page.locator('#navMobile a[href="#espaces"]').click()
            page.wait_for_timeout(1200)
            page.screenshot(path=str(ARTIFACTS / "chateau-sainte-anne-mobile-spaces.png"))

            # Mobile continuous scroll remainder
            for sel in ["#atouts", "#tarifs", "#contact"]:
                top = section_top(page, sel) - 30
                smooth_scroll(page, top, 1400)
                page.wait_for_timeout(300)

            page.locator("#eventDate").click()
            page.wait_for_timeout(400)
            page.locator("#guestsIncrease").click()
            page.wait_for_timeout(400)
            page.screenshot(path=str(ARTIFACTS / "chateau-sainte-anne-mobile-contact.png"))

            page.close()
            video = Path(page.video.path()) if page.video else None
            context.close()
            browser.close()

            if video and video.exists():
                if VIDEO_PATH.exists():
                    VIDEO_PATH.unlink()
                video.replace(VIDEO_PATH)
                results["video"] = str(VIDEO_PATH)
                results["video_bytes"] = VIDEO_PATH.stat().st_size
            else:
                # fallback: newest webm in artifacts from this run
                candidates = sorted(
                    ARTIFACTS.glob("*.webm"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                )
                if candidates:
                    if VIDEO_PATH.exists() and candidates[0] != VIDEO_PATH:
                        VIDEO_PATH.unlink()
                    if candidates[0] != VIDEO_PATH:
                        candidates[0].replace(VIDEO_PATH)
                    results["video"] = str(VIDEO_PATH)
                    results["video_bytes"] = VIDEO_PATH.stat().st_size
                else:
                    results["errors"].append("Walkthrough video missing")
    finally:
        server.shutdown()

    out = ARTIFACTS / "chateau-sainte-anne-verify.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
    broken = [i for i in results["images"] if not i["ok"]]
    print(f"Images: {len(results['images'])} total, {len(broken)} broken")
    if results["errors"]:
        print("ERRORS:")
        for e in results["errors"]:
            print(" -", e)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
