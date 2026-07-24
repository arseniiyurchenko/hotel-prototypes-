#!/usr/bin/env python3
"""Visual verification for Villa Decius conference venue prototype."""

from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
URL = "http://127.0.0.1:8765/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)


def main():
    issues = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(URL, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(2000)

        # Image load check
        broken = page.evaluate(
            """() => Array.from(document.images).filter(img => !img.complete || img.naturalWidth === 0)
              .map(img => img.src)"""
        )
        if broken:
            issues.append(f"Broken images: {broken}")
        else:
            print(f"OK: all {page.evaluate('() => document.images.length')} images loaded")

        # Header spacing
        spacing = page.evaluate(
            """() => {
              const brand = document.querySelector('.brand');
              const cta = document.querySelector('.header-cta');
              const br = brand.getBoundingClientRect();
              const cr = cta.getBoundingClientRect();
              return { left: br.left, rightGap: window.innerWidth - cr.right, headerH: document.querySelector('.site-header').offsetHeight };
            }"""
        )
        print(f"Header spacing: left={spacing['left']:.1f}px rightGap={spacing['rightGap']:.1f}px")
        if spacing["left"] < 24 or spacing["rightGap"] < 24:
            issues.append(f"Header too cramped: {spacing}")

        # Smooth scroll via nav
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(300)
        page.click('.nav-desktop a[href="#spaces"]')
        page.wait_for_timeout(900)
        scroll_y = page.evaluate("() => window.scrollY")
        spaces_top = page.evaluate("() => document.getElementById('spaces').offsetTop")
        print(f"Nav scroll: scrollY={scroll_y}, spacesTop≈{spaces_top}")
        if scroll_y < 100:
            issues.append("Smooth scroll to #spaces did not move page meaningfully")

        # Enquiry widget
        tomorrow = page.evaluate(
            "() => { const d=new Date(); d.setDate(d.getDate()+2); return d.toISOString().slice(0,10); }"
        )
        page.fill("#eventDate", tomorrow)
        page.select_option("#eventType", "banquet")
        page.select_option("#guestCount", "21-50")
        page.click("button.enquiry-submit")
        page.wait_for_timeout(400)
        note = page.inner_text("#enquiryNote")
        print(f"Enquiry note: {note[:80]}")
        if "prototype" not in note.lower() and "thanks" not in note.lower():
            issues.append(f"Enquiry widget note unexpected: {note}")

        # Sections present
        for sid in ["hero", "enquiry", "spaces", "amenities", "gallery", "location", "trust", "footer"]:
            if not page.query_selector(f"#{sid}"):
                issues.append(f"Missing section #{sid}")

        page.screenshot(path=str(ARTIFACTS / "villa-decjusza-desktop.png"), full_page=True)

        # Mobile
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(400)
        page.click("#menuToggle")
        page.wait_for_timeout(500)
        page.screenshot(path=str(ARTIFACTS / "villa-decjusza-mobile.png"), full_page=False)
        mobile_spacing = page.evaluate(
            """() => {
              const brand = document.querySelector('.brand');
              const cta = document.querySelector('.header-cta');
              return { left: brand.getBoundingClientRect().left, rightGap: window.innerWidth - cta.getBoundingClientRect().right };
            }"""
        )
        print(f"Mobile header spacing: {mobile_spacing}")
        if mobile_spacing["left"] < 20 or mobile_spacing["rightGap"] < 20:
            issues.append(f"Mobile header cramped: {mobile_spacing}")

        # Overlap check (simple)
        overlap = page.evaluate(
            """() => {
              const hero = document.querySelector('#hero h1');
              const enquiry = document.querySelector('#enquiry');
              if (!hero || !enquiry) return null;
              const a = hero.getBoundingClientRect();
              const b = enquiry.getBoundingClientRect();
              const hit = !(a.bottom < b.top || a.top > b.bottom || a.right < b.left || a.left > b.right);
              return { hit, aBottom: a.bottom, bTop: b.top };
            }"""
        )
        print(f"Hero/enquiry overlap check: {overlap}")

        browser.close()

    if issues:
        print("ISSUES:")
        for i in issues:
            print(" -", i)
        raise SystemExit(1)
    print("VERIFY PASS")


if __name__ == "__main__":
    main()
