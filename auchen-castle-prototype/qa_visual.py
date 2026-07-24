#!/usr/bin/env python3
"""Thorough visual QA for Auchen Castle prototype."""

import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8772/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)

results = {"checks": [], "errors": [], "warnings": []}


def check(name, ok, detail=""):
    results["checks"].append({"name": name, "ok": ok, "detail": detail})
    if not ok:
        results["errors"].append(f"{name}: {detail}")
    print(("PASS" if ok else "FAIL"), "-", name, detail)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(2000)

        # --- Images ---
        page.evaluate("() => { document.documentElement.style.scrollBehavior = 'auto'; window.scrollTo(0, document.body.scrollHeight); }")
        page.wait_for_timeout(1500)
        page.evaluate("() => window.scrollTo(0, 0)")
        page.wait_for_timeout(500)
        for sel in ["#spaces", "#gallery", "#location", "#contact"]:
            page.locator(sel).scroll_into_view_if_needed()
            page.wait_for_timeout(700)
        page.wait_for_timeout(1000)

        imgs = page.locator("img").all()
        broken = []
        for img in imgs:
            src = img.get_attribute("src") or ""
            ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
            if not ok:
                broken.append(src)
        check("all images load", len(broken) == 0, f"{len(imgs)} imgs, broken={broken}")

        # --- Header spacing ---
        page.evaluate("() => window.scrollTo(0, 0)")
        page.wait_for_timeout(400)
        metrics = page.evaluate(
            """() => {
              const header = document.querySelector('.site-header');
              const brand = document.querySelector('.brand');
              const phone = document.querySelector('.header-phone');
              const br = brand.getBoundingClientRect();
              const pr = phone.getBoundingClientRect();
              const hr = header.getBoundingClientRect();
              return {
                logoLeft: br.left,
                phoneRightGap: window.innerWidth - pr.right,
                headerHeight: hr.height,
                logoTop: br.top,
                phoneTop: pr.top
              };
            }"""
        )
        check(
            "logo spacing from left edge",
            metrics["logoLeft"] >= 16,
            json.dumps(metrics),
        )
        check(
            "phone/CTA spacing from right edge",
            metrics["phoneRightGap"] >= 16,
            json.dumps(metrics),
        )

        page.screenshot(path=str(ARTIFACTS / "qa-desktop-hero.png"))

        # --- Smooth anchor navigation ---
        anchors = ["#spaces", "#features", "#packages", "#gallery", "#location", "#inquiry"]
        for href in anchors:
            # Instant reset — do not fight an in-progress smooth scroll
            page.evaluate(
                """() => {
                  document.documentElement.style.scrollBehavior = 'auto';
                  window.scrollTo(0, 0);
                }"""
            )
            page.wait_for_timeout(300)
            target = href[1:]
            start_y = page.evaluate("() => window.scrollY")
            t0 = time.time()
            page.locator(f'.nav-desktop a[href="{href}"]').click(timeout=3000)
            landed = False
            samples = []
            for _ in range(50):
                page.wait_for_timeout(100)
                info = page.evaluate(
                    f"""() => {{
                      const el = document.getElementById('{target}');
                      const headerH = document.querySelector('.site-header').getBoundingClientRect().height;
                      const top = el.getBoundingClientRect().top;
                      return {{ top, headerH, y: window.scrollY }};
                    }}"""
                )
                samples.append(info)
                if info["top"] >= info["headerH"] - 24 and info["top"] < info["headerH"] + 160:
                    page.wait_for_timeout(200)
                    landed = True
                    break
            elapsed = time.time() - t0
            travel = abs((samples[-1]["y"] if samples else 0) - start_y)
            # Short hops (e.g. enquiry near top) may finish under 150ms of animation setup
            timing_ok = elapsed >= 0.15 or travel < 200
            check(
                f"smooth scroll to {href}",
                landed and timing_ok,
                f"elapsed={elapsed:.3f}s travel={travel:.0f} landed={landed} final={samples[-1] if samples else None}",
            )
            overlap = page.evaluate(
                f"""() => {{
                  const el = document.getElementById('{target}');
                  const h = document.querySelector('.site-header').getBoundingClientRect().height;
                  const top = el.getBoundingClientRect().top;
                  const heading = el.querySelector('h2, .section-head h2, h3');
                  const ht = heading ? heading.getBoundingClientRect().top : top;
                  return {{ sectionTop: top, headingTop: ht, headerH: h, headingVisible: ht >= h - 8 }};
                }}"""
            )
            if not overlap["headingVisible"]:
                results["warnings"].append(f"heading may be under header for {href}: {overlap}")
                print("WARN - heading under header", href, overlap)
            else:
                print("PASS - heading clear of header", href, overlap)

        # --- Enquiry widget ---
        page.locator("#inquiry").scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        event_date = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+21); return d.toISOString().split('T')[0]; }"
        )
        page.locator("#eventDate").fill(event_date)
        page.locator("#delegateBand").select_option(label="51 to 75")
        page.locator("#eventType").select_option(label="Conference / meeting")
        page.locator("#packageInterest").select_option(label="Day Delegate (£45 pp)")
        page.locator("#inquiryForm button[type='submit']").click()
        page.wait_for_timeout(400)
        check(
            "enquiry form submit shows success",
            page.locator("#inquirySuccess.show").count() == 1,
            "",
        )
        page.screenshot(path=str(ARTIFACTS / "qa-desktop-inquiry.png"))

        # --- Full page layout scan ---
        overflows = page.evaluate(
            """() => {
              const issues = [];
              const docW = document.documentElement.clientWidth;
              document.querySelectorAll('section, .inquiry, .hero, header, footer').forEach(el => {
                const r = el.getBoundingClientRect();
                if (r.width > docW + 2) issues.push({tag: el.id || el.className, w: r.width, docW});
              });
              // empty sections: no text and no images
              document.querySelectorAll('section').forEach(el => {
                const text = (el.innerText || '').trim();
                const imgs = el.querySelectorAll('img').length;
                if (text.length < 20 && imgs === 0) issues.push({empty: el.id || el.className});
              });
              return issues;
            }"""
        )
        check("no horizontal overflow / empty sections", len(overflows) == 0, json.dumps(overflows))

        page.evaluate("() => window.scrollTo(0,0)")
        page.wait_for_timeout(300)
        page.screenshot(path=str(ARTIFACTS / "qa-desktop-full.png"), full_page=True)

        # --- Mobile ---
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(600)
        page.evaluate("() => window.scrollTo(0,0)")
        page.wait_for_timeout(400)

        mobile_metrics = page.evaluate(
            """() => {
              const brand = document.querySelector('.brand');
              const toggle = document.querySelector('#menuToggle');
              const br = brand.getBoundingClientRect();
              const tr = toggle.getBoundingClientRect();
              return {
                logoLeft: br.left,
                toggleRightGap: window.innerWidth - tr.right,
                toggleVisible: getComputedStyle(toggle).display !== 'none'
              };
            }"""
        )
        check(
            "mobile header spacing",
            mobile_metrics["logoLeft"] >= 14
            and mobile_metrics["toggleRightGap"] >= 14
            and mobile_metrics["toggleVisible"],
            json.dumps(mobile_metrics),
        )

        page.locator("#menuToggle").click()
        page.wait_for_timeout(400)
        check("mobile nav opens", page.locator("#navMobile.open").count() == 1, "")
        page.screenshot(path=str(ARTIFACTS / "qa-mobile-menu.png"))
        page.locator("#navClose").click()
        page.wait_for_timeout(300)

        page.locator("#inquiry").scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        # Re-interact selects on mobile
        page.locator("#delegateBand").select_option(label="26 to 50")
        page.locator("#eventType").select_option(label="Team-building")
        page.screenshot(path=str(ARTIFACTS / "qa-mobile-inquiry.png"))

        page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(600)
        page.screenshot(path=str(ARTIFACTS / "qa-mobile-full.png"), full_page=True)

        mob_overflow = page.evaluate(
            """() => {
              const issues = [];
              const docW = document.documentElement.clientWidth;
              if (document.documentElement.scrollWidth > docW + 2) {
                issues.push({scrollWidth: document.documentElement.scrollWidth, docW});
              }
              return issues;
            }"""
        )
        check("mobile no horizontal scroll", len(mob_overflow) == 0, json.dumps(mob_overflow))

        browser.close()

    print(json.dumps(results, indent=2))
    if results["errors"]:
        print("VERIFICATION FAILED")
        sys.exit(1)
    print("QA PASSED")
    if results["warnings"]:
        print("WARNINGS:", results["warnings"])
        sys.exit(2)


if __name__ == "__main__":
    main()
