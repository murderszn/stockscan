#!/usr/bin/env python3
"""Scrape Micro Center product stock and write status.json for GitHub Pages."""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

STORE_ID = "151"
STORE_LABEL = "Chicago, IL"
STORE_ADDRESS = "2645 N Elston Ave"
PRODUCT_URL = (
    "https://www.microcenter.com/product/690207/"
    "ubiquiti-pro-max-16-poe-25g-1g-managed-network-switch-with-etherlighting"
)
PRODUCT_NAME = "Ubiquiti Pro Max 16 PoE"
PRODUCT_SKU = "690207"
OUT = Path(__file__).resolve().parent / "status.json"


def parse_stock(page_source: str, store_id: str = STORE_ID) -> tuple[bool | None, str]:
    # 1. Parse var inventory array in JavaScript
    m_inv = re.search(r"var\s+inventory\s*=\s*(\[\s*\{.*?\}\s*\])", page_source)
    if m_inv:
        try:
            inv_data = json.loads(m_inv.group(1))
            for item in inv_data:
                if str(item.get("storeNumber")) == str(store_id):
                    qoh = int(item.get("qoh", 0))
                    if qoh > 0:
                        return True, f"IN STOCK ({qoh})" if qoh > 1 else "IN STOCK"
                    else:
                        return False, "OUT OF STOCK"
        except Exception:
            pass

    # 2. Parse dataLayer object
    m_dl = re.search(r"['\"]inStock['\"]?\s*:\s*['\"]?(True|False)['\"]?", page_source, re.I)
    if m_dl:
        in_stock = m_dl.group(1).lower() == "true"
        return in_stock, ("IN STOCK" if in_stock else "OUT OF STOCK")

    # 3. Parse JSON-LD schema
    if "schema.org/InStock" in page_source:
        return True, "IN STOCK"
    if "schema.org/OutOfStock" in page_source:
        return False, "OUT OF STOCK"

    # 4. Fallback HTML text checks
    lower = page_source.lower()
    if "out of stock" in lower or "sold out" in lower:
        return False, "OUT OF STOCK"
    if "add to cart" in lower and "in stock" in lower:
        return True, "IN STOCK"

    return None, "SIGNAL LOST"


def parse_price(page_source: str) -> str | None:
    patterns = [
        r"['\"]productPrice['\"]?\s*[:=]\s*['\"]([0-9]+(?:\.[0-9]{2})?)['\"]",
        r'["\']price["\']\s*:\s*["\']?([0-9]+(?:\.[0-9]{2})?)["\']?',
        r'itemprop=["\']price["\'][^>]*content=["\']([0-9]+(?:\.[0-9]{2})?)["\']',
        r'id=["\']data-price["\'][^>]*content=["\']([0-9]+(?:\.[0-9]{2})?)["\']',
    ]
    for pat in patterns:
        m = re.search(pat, page_source, re.I)
        if m:
            return f"${m.group(1)}"
    return None


def is_cloudflare_challenge(html: str) -> bool:
    m = re.search(r"<title>(.*?)</title>", html, re.I)
    title = m.group(1).lower() if m else ""
    keywords = ["just a moment", "attention required", "access denied", "cloudflare"]
    return any(kw in title for kw in keywords)


def scrape_via_curl() -> tuple[bool | None, str, str | None]:
    try:
        from curl_cffi import requests
    except ImportError:
        raise RuntimeError("curl_cffi is not installed")

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "max-age=0",
        "Cookie": f"storeSelected={STORE_ID}",
        "Referer": "https://www.microcenter.com/",
        "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="124", "Google Chrome";v="124"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"macOS"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    }

    res = requests.get(PRODUCT_URL, impersonate="chrome124", headers=headers, timeout=15)
    if res.status_code != 200:
        raise RuntimeError(f"HTTP response status code {res.status_code}")

    html = res.text
    if is_cloudflare_challenge(html):
        raise RuntimeError("Cloudflare bot protection challenge triggered via curl_cffi")

    in_stock, message = parse_stock(html, STORE_ID)
    price = parse_price(html)
    return in_stock, message, price


def scrape_via_playwright() -> tuple[bool | None, str, str | None]:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
            ],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1400, "height": 900},
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
            },
        )
        page = context.new_page()
        page.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            """
        )

        context.add_cookies(
            [
                {
                    "name": "storeSelected",
                    "value": STORE_ID,
                    "domain": ".microcenter.com",
                    "path": "/",
                    "secure": True,
                    "httpOnly": False,
                }
            ]
        )

        try:
            page.goto("https://www.microcenter.com", wait_until="domcontentloaded", timeout=30000)
            time.sleep(1)
        except Exception:
            pass

        page.goto(PRODUCT_URL, wait_until="domcontentloaded", timeout=60000)

        for _ in range(20):
            title = page.title()
            if "just a moment" not in title.lower() and "attention required" not in title.lower():
                break
            time.sleep(1)

        src = page.content()
        browser.close()

        if is_cloudflare_challenge(src):
            raise RuntimeError("Cloudflare bot protection challenge triggered via Playwright")

        in_stock, message = parse_stock(src, STORE_ID)
        price = parse_price(src)
        return in_stock, message, price


def scrape_with_retry(max_retries: int = 3) -> tuple[bool | None, str, str | None]:
    last_err: Exception | None = None
    # Method 1: Try curl_cffi first (TLS fingerprint impersonation)
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Scraping via curl_cffi (attempt {attempt}/{max_retries})...")
            return scrape_via_curl()
        except Exception as e:
            last_err = e
            print(f"curl_cffi attempt {attempt} failed: {e}")
            if attempt < max_retries:
                time.sleep(2 * attempt)

    # Method 2: Fallback to Playwright if curl_cffi fails
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Scraping via Playwright fallback (attempt {attempt}/{max_retries})...")
            return scrape_via_playwright()
        except Exception as e:
            last_err = e
            print(f"Playwright attempt {attempt} failed: {e}")
            if attempt < max_retries:
                time.sleep(3 * attempt)

    raise last_err or RuntimeError("Scrape failed all retries")


def scrape() -> dict:
    # Read existing status to preserve known state on error
    existing_status = {}
    if OUT.exists():
        try:
            existing_status = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:
            pass

    status = {
        "product": PRODUCT_NAME,
        "sku": PRODUCT_SKU,
        "url": PRODUCT_URL,
        "store_id": STORE_ID,
        "store_label": STORE_LABEL,
        "store_address": STORE_ADDRESS,
        "price": existing_status.get("price"),
        "in_stock": existing_status.get("in_stock"),
        "message": existing_status.get("message", "AWAITING SCAN"),
        "last_checked": existing_status.get("last_checked"),
        "checking": False,
        "error": None,
    }

    try:
        in_stock, message, price = scrape_with_retry(max_retries=3)
        status.update(
            {
                "in_stock": in_stock,
                "message": message,
                "price": price or existing_status.get("price"),
                "last_checked": datetime.now(timezone.utc).isoformat(),
                "error": None,
            }
        )
    except Exception as e:
        status.update(
            {
                "error": str(e),
                "last_checked": datetime.now(timezone.utc).isoformat(),
            }
        )
        if status.get("in_stock") is None:
            status["message"] = "SCAN FAILED"
    return status


def main() -> None:
    status = scrape()
    OUT.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
