#!/usr/bin/env python3
"""Verify Hotel Santa prototype: images, layout spacing, smooth scroll, booking UI."""

from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/index.html"
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)


def main():
    issues = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(URL, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(2500)

        # Image load check
        img_report = page.evaluate(
            """() => {
              const imgs = [...document.images];
              return imgs.map(img => ({
                src: img.currentSrc || img.src,
                complete: img.complete,
                w: img.naturalWidth,
                h: img.naturalHeight,
                alt: img.alt
              }));
            }"""
        )
        broken = [i for i in img_report if not i["complete"] or i["w"] == 0]
        print(f"Images total: {len(img_report)}, broken: {len(broken)}")
        for b in broken:
            print(" BROKEN:", b["src"])
            issues.append(f"broken image: {b['src']}")

        # Header spacing
        spacing = page.evaluate(
            """() => {
              const header = document.getElementById('header');
              const brand = document.querySelector('.brand');
              const cta = document.querySelector('.header-cta');
              const hr = header.getBoundingClientRect();
              const br = brand.getBoundingClientRect();
              const cr = cta.getBoundingClientRect();
              return {
                leftGap: br.left - hr.left,
                rightGap: hr.right - cr.right,
                sticky: getComputedStyle(header).position,
                scrollBehavior: getComputedStyle(document.documentElement).scrollBehavior
              };
            }"""
        )
        print("Header spacing:", spacing)
        if spacing["leftGap"] < 28:
            issues.append(f"logo too close to left edge: {spacing['leftGap']}px")
        if spacing["rightGap"] < 28:
            issues.append(f"CTA too close to right edge: {spacing['rightGap']}px")
        if spacing["scrollBehavior"] != "smooth":
            issues.append(f"scroll-behavior is {spacing['scrollBehavior']}, expected smooth")

        page.screenshot(path=str(ARTIFACTS / "hotel-santa-desktop-hero.png"), full_page=False)

        # Smooth anchor navigation
        before = page.evaluate("() => window.scrollY")
        page.click('a.header-cta')
        page.wait_for_timeout(900)
        mid = page.evaluate("() => window.scrollY")
        page.wait_for_timeout(900)
        after = page.evaluate("() => window.scrollY")
        print(f"Smooth scroll CTA: before={before}, mid={mid}, after={after}")
        if after < 100:
            issues.append("CTA did not scroll to booking section")
        # mid should differ from before/after if smooth (not always guaranteed in headless)
        booking_top = page.evaluate(
            "() => Math.abs(document.getElementById('booking').getBoundingClientRect().top)"
        )
        print(f"Booking section distance from top after CTA: {booking_top}")
        if booking_top > 120:
            issues.append(f"booking not near viewport after CTA scroll: {booking_top}")

        for href in ["#rooms", "#amenities", "#gallery", "#location", "#trust"]:
            page.click(f'.nav-desktop a[href="{href}"]')
            page.wait_for_timeout(1100)
            dist = page.evaluate(
                f"() => Math.abs(document.querySelector('{href}').getBoundingClientRect().top)"
            )
            print(f"Nav {href} distance from top: {dist}")
            if dist > 140:
                issues.append(f"nav {href} did not land near section (dist={dist})")

        # Booking widget
        tomorrow = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+2); return d.toISOString().split('T')[0]; }"
        )
        checkout = page.evaluate(
            "() => { const d = new Date(); d.setDate(d.getDate()+5); return d.toISOString().split('T')[0]; }"
        )
        page.fill("#checkin", tomorrow)
        page.fill("#checkout", checkout)
        page.click("#guestTrigger")
        page.wait_for_timeout(400)
        open_state = page.evaluate("() => document.getElementById('guestDropdown').classList.contains('open')")
        if not open_state:
            issues.append("guest dropdown did not open")
        page.click("#adultsPlus")
        page.click("#childrenPlus")
        summary = page.inner_text("#guestSummary")
        print("Guest summary:", summary)
        if "3 adults" not in summary or "1 child" not in summary:
            issues.append(f"unexpected guest summary: {summary}")

        page.screenshot(path=str(ARTIFACTS / "hotel-santa-booking.png"), full_page=False)
        page.screenshot(path=str(ARTIFACTS / "hotel-santa-desktop-full.png"), full_page=True)

        # Mobile
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(600)
        page.evaluate("window.scrollTo(0,0)")
        page.wait_for_timeout(400)
        mobile_spacing = page.evaluate(
            """() => {
              const header = document.getElementById('header');
              const brand = document.querySelector('.brand');
              const cta = document.querySelector('.header-cta');
              const hr = header.getBoundingClientRect();
              const br = brand.getBoundingClientRect();
              const cr = cta.getBoundingClientRect();
              return { leftGap: br.left - hr.left, rightGap: hr.right - cr.right };
            }"""
        )
        print("Mobile header spacing:", mobile_spacing)
        if mobile_spacing["leftGap"] < 24 or mobile_spacing["rightGap"] < 24:
            issues.append(f"mobile header spacing tight: {mobile_spacing}")
        page.screenshot(path=str(ARTIFACTS / "hotel-santa-mobile.png"), full_page=False)

        # Overlap heuristics
        page.set_viewport_size({"width": 1280, "height": 800})
        page.evaluate("window.scrollTo(0,0)")
        overlap = page.evaluate(
            """() => {
              const sections = ['hero','booking','rooms','amenities','gallery','location','trust','footer'];
              const empty = [];
              for (const id of sections) {
                const el = document.getElementById(id);
                if (!el) { empty.push('missing:'+id); continue; }
                if (el.getBoundingClientRect().height < 40) empty.push('short:'+id);
              }
              return empty;
            }"""
        )
        print("Section check:", overlap)
        issues.extend(overlap)

        browser.close()

    if issues:
        print("ISSUES:")
        for i in issues:
            print(" -", i)
        raise SystemExit(1)
    print("VERIFICATION OK")


if __name__ == "__main__":
    main()
