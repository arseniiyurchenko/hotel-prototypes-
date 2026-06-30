#!/usr/bin/env python3
"""Verify Skrundas muiža homepage prototype."""

import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8766/index.html"


def main():
    results = {"images_ok": [], "images_broken": [], "checks": []}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(URL, wait_until="networkidle", timeout=60000)

        imgs = page.eval_on_selector_all(
            "img",
            "els => els.map(el => ({src: el.src, ok: el.complete && el.naturalWidth > 0}))",
        )
        for img in imgs:
            (results["images_ok"] if img["ok"] else results["images_broken"]).append(img["src"])

        page.fill("#checkin", "2026-08-01")
        page.fill("#checkout", "2026-08-04")
        page.select_option("#guests", "4")
        results["checks"].append("booking widget ok")

        page.set_viewport_size({"width": 390, "height": 844})
        page.click("#menuToggle")
        page.click("#menuClose")
        results["checks"].append("mobile menu ok")

        browser.close()

    print(json.dumps(results, indent=2))
    if results["images_broken"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
