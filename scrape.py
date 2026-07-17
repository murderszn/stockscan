#!/usr/bin/env python3
"""Scrape Micro Center product stock and write status.json for GitHub Pages."""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

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


def parse_stock(page_source: str) -> tuple[bool | None, str]:
    m = re.search(r"inStock['\"]?\s*[:=]\s*['\"]?(True|False)", page_source, re.I)
    if m:
        in_stock = m.group(1).lower() == "true"
        return in_stock, ("IN STOCK" if in_stock else "OUT OF STOCK")
    lower = page_source.lower()
    if "out of stock" in lower or "sold out" in lower:
        return False, "OUT OF STOCK"
    if "add to cart" in lower and "in stock" in lower:
        return True, "IN STOCK"
    return None, "SIGNAL LOST"


def parse_price(page_source: str) -> str | None:
    patterns = [
        r"productPrice['\"]?\s*[:=]\s*['\"]([0-9]+(?:\.[0-9]{2})?)['\"]",
        r'"price"\s*:\s*"?([0-9]+(?:\.[0-9]{2})?)"?',
        r'itemprop=["\']price["\'][^>]*content=["\']([0-9]+(?:\.[0-9]{2})?)["\']',
    ]
    for pat in patterns:
        m = re.search(pat, page_source, re.I)
        if m:
            return f"${m.group(1)}"
    return None


def scrape() -> dict:
    status = {
        "product": PRODUCT_NAME,
        "sku": PRODUCT_SKU,
        "url": PRODUCT_URL,
        "store_id": STORE_ID,
        "store_label": STORE_LABEL,
        "store_address": STORE_ADDRESS,
        "price": None,
        "in_stock": None,
        "message": "AWAITING SCAN",
        "last_checked": None,
        "checking": False,
        "error": None,
    }
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/150.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1400, "height": 900},
            )
            page = context.new_page()
            page.goto("https://www.microcenter.com", wait_until="domcontentloaded", timeout=60000)
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
            page.goto(PRODUCT_URL, wait_until="domcontentloaded", timeout=90000)
            for _ in range(45):
                title = page.title()
                if "just a moment" not in title.lower() and "moment" not in title.lower():
                    break
                time.sleep(1)
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            time.sleep(1)
            src = page.content()
            in_stock, message = parse_stock(src)
            price = parse_price(src)
            browser.close()

        status.update(
            {
                "in_stock": in_stock,
                "message": message,
                "price": price,
                "last_checked": datetime.now(timezone.utc).isoformat(),
                "error": None,
            }
        )
    except Exception as e:
        status.update(
            {
                "message": "SCAN FAILED",
                "error": str(e),
                "last_checked": datetime.now(timezone.utc).isoformat(),
            }
        )
    return status


def main() -> None:
    status = scrape()
    OUT.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
