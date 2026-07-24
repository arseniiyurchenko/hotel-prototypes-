#!/usr/bin/env python3
"""Verify Château Sainte-Anne prototype: images, enquiry widget, multi-viewport screenshots."""

from __future__ import annotations

import http.server
import json
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
ARTIFACTS = Path("/opt/cursor/artifacts")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
PORT = 8765

results: dict = {"images": [], "interactions": [], "errors": [], "viewports": []}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, format, *args):  # noqa: A003
        pass


def main() -> int:
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{PORT}/index.html"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=120000)
            page.wait_for_timeout(1000)

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
            page.wait_for_timeout(400)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(400)

            for img in page.locator("img").all():
                src = img.get_attribute("src") or ""
                ok = img.evaluate("el => el.complete && el.naturalWidth > 0")
                results["images"].append({"src": src[:140], "ok": ok})
                if not ok:
                    results["errors"].append(f"Broken image: {src}")

            brand = page.locator(".hero-brand").inner_text().strip()
            if "Château Sainte-Anne" not in brand:
                results["errors"].append("Hero brand missing venue name")

            page.screenshot(path=str(ARTIFACTS / "chateau-sainte-anne-desktop-hero.png"))
            page.screenshot(
                path=str(ARTIFACTS / "chateau-sainte-anne-desktop-full.png"),
                full_page=True,
            )
            results["viewports"].append("desktop-1280")

            page.locator("#contact").scroll_into_view_if_needed()
            page.locator("#name").fill("Camille Dupont")
            page.locator("#email").fill("camille@example.com")
            page.locator("#eventDate").fill("2026-09-12")
            page.locator("#altDate").fill("2026-09-19")
            page.locator("#eventType").select_option("mariage")
            page.locator("#guestsIncrease").click()
            page.locator("#guestsDecrease").click()
            page.locator("#submitEnquiry").click()
            page.wait_for_timeout(400)
            status = page.locator("#formStatus").inner_text()
            results["interactions"].append(f"enquiry form: {status[:120]}")
            if "Nathalie" not in status and "prototype" not in status.lower():
                results["errors"].append(f"Unexpected form status: {status}")

            page.set_viewport_size({"width": 390, "height": 844})
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(400)
            page.locator("#menuToggle").click()
            page.wait_for_selector("#navMobile.open")
            page.locator('#navMobile a[href="#espaces"]').click(force=True)
            page.wait_for_timeout(700)
            page.screenshot(path=str(ARTIFACTS / "chateau-sainte-anne-mobile-spaces.png"))
            results["viewports"].append("mobile-390")

            browser.close()
    finally:
        server.shutdown()

    out = ARTIFACTS / "chateau-sainte-anne-verify.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
    broken = [i for i in results["images"] if not i["ok"]]
    print(f"Images: {len(results['images'])} total, {len(broken)} broken")
    if results["errors"]:
        for e in results["errors"]:
            print("ERROR:", e)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
