#!/usr/bin/env python3
"""Verify searate/index.html and record a walkthrough video."""
import asyncio
import os
import subprocess
import sys
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent
HTML = ROOT / "index.html"
VIDEO_DIR = Path("/opt/cursor/artifacts")
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_PATH = VIDEO_DIR / "roja-hotel-prototype-walkthrough.webm"


async def main():
    issues = []
    url = HTML.as_uri()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(VIDEO_DIR),
            record_video_size={"width": 1280, "height": 720},
        )
        page = await context.new_page()

        print(f"Loading {url}")
        await page.goto(url, wait_until="networkidle")

        # Verify images
        img_results = await page.evaluate(
            """() => Array.from(document.images).map(img => ({
                src: img.currentSrc || img.src,
                ok: img.complete && img.naturalWidth > 0,
                w: img.naturalWidth,
                h: img.naturalHeight
            }))"""
        )
        broken = [i for i in img_results if not i["ok"]]
        print(f"Images: {len(img_results)} total, {len(broken)} broken")
        for img in img_results:
            status = "OK" if img["ok"] else "BROKEN"
            print(f"  [{status}] {img['src'][:90]}...")
        if broken:
            issues.append(f"{len(broken)} broken image(s)")

        # Hero scroll
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(800)

        # Booking widget interaction
        await page.locator("#booking").scroll_into_view_if_needed()
        await page.wait_for_timeout(600)
        await page.locator("#checkin").click()
        await page.wait_for_timeout(500)
        await page.locator("#checkout").click()
        await page.wait_for_timeout(500)
        await page.locator("#guestsDisplay").click()
        await page.wait_for_timeout(400)
        await page.locator('[data-target="adults"][data-action="increase"]').click()
        await page.locator('[data-target="children"][data-action="increase"]').click()
        await page.wait_for_timeout(600)

        # Scroll sections
        for section in ["#rooms", "#amenities", "#gallery", "#location", "#trust", "#contact"]:
            await page.locator(section).scroll_into_view_if_needed()
            await page.wait_for_timeout(700)

        # Mobile viewport
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(500)
        await page.locator("#menuToggle").click()
        await page.wait_for_selector('#navMobile.open')
        await page.wait_for_timeout(400)
        await page.locator('#navMobile a[href="#rooms"]').click(force=True)
        await page.wait_for_timeout(800)
        await page.locator("#booking").scroll_into_view_if_needed()
        await page.wait_for_timeout(600)
        await page.locator("#guestsDisplay").click()
        await page.wait_for_timeout(500)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(800)

        video = page.video
        await page.close()
        await context.close()
        await browser.close()

        if video:
            raw_path = await video.path()
            if raw_path and os.path.exists(raw_path):
                subprocess.run(
                    [
                        "ffmpeg", "-y", "-i", raw_path,
                        "-c:v", "libvpx-vp9", "-b:v", "1M",
                        str(VIDEO_PATH),
                    ],
                    check=True,
                    capture_output=True,
                )
                print(f"Video saved to {VIDEO_PATH}")

    if issues:
        print("ISSUES:", "; ".join(issues))
        sys.exit(1)

    print("Verification passed.")


if __name__ == "__main__":
    asyncio.run(main())
