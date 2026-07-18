# STOCKSCAN // Micro Center Inventory HUD

<p align="center">
  <img src="favicon.svg" width="80" height="80" alt="STOCKSCAN Logo" />
</p>

<p align="center">
  <b>A sleek, cyberpunk-inspired real-time stock tracker for Micro Center inventory.</b>
</p>

<p align="center">
  <a href="https://murderszn.github.io/stockscan/"><img src="https://img.shields.io/badge/LIVE_HUD-ONLINE-00e8ff?style=for-the-badge&logo=github&logoColor=white" alt="Live Page" /></a>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12" />
  <img src="https://img.shields.io/badge/Bypass-Cloudflare_WAF-FF6600?style=for-the-badge&logo=cloudflare&logoColor=white" alt="Cloudflare Bypass" />
  <img src="https://img.shields.io/badge/Automated-GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white" alt="GitHub Actions" />
</p>

---

## 🛰️ Overview

**STOCKSCAN** monitors store inventory and pricing for high-demand hardware at **Micro Center** (configured for **Ubiquiti Pro Max 16 PoE**, SKU `690207` at **Chicago, IL · 2645 N Elston Ave**). 

It runs on an automated **30-minute cadence via GitHub Actions**, executing a stealth scraper that bypasses Cloudflare anti-bot checks and publishes updates to a GitHub Pages dashboard.

👉 **Live Dashboard:** [https://murderszn.github.io/stockscan/](https://murderszn.github.io/stockscan/)

---

## ✨ Features

- **⚡ Cyberpunk HUD Interface (`index.html`)**: Glassmorphism design with scanlines, dynamic color states (Green = In Stock, Red = Out of Stock, Amber = Scanning), tabular metrics, and single-click manual refresh.
- **🛡️ Cloudflare WAF Evasion (`curl_cffi`)**: Uses browser TLS fingerprint impersonation (`chrome124`, `safari17`) to pass Cloudflare WAF checks without triggering 503 errors or bot challenges.
- **🏬 Multi-Layer Inventory Extraction**:
  - `var inventory`: Parses Micro Center's JavaScript array to get exact **Quantity On Hand (`qoh`)** per store ID.
  - `dataLayer`: Extracts real-time `inStock` states and price tags.
  - `JSON-LD`: Fallback schema microdata parsing (`schema.org/InStock`).
  - Playwright fallback with browser stealth shims.
- **🤖 Automated GitHub Actions Workflow**: Runs every 30 minutes on a cron schedule, auto-committing status changes with `[skip ci]` to prevent deployment loops.
- **💾 Fault-Tolerant State Preservation**: Preserves last known stock and price data on temporary network glitches rather than clearing state.

---

## ⚙️ How It Works

```mermaid
flowchart TD
    A["⏱️ GitHub Actions Cron\n(Every 30 Mins)"] -->|Triggers Runner| B["🐍 scrape.py Execution"]
    B -->|TLS Impersonation (curl_cffi)| C["🏬 Micro Center Store #151\n(Chicago, IL)"]
    C -->|Extracts Inventory & Price| B
    B -->|Writes Data| D["📄 status.json"]
    D -->|Commit & Deploy| E["🌐 GitHub Pages Hosting"]
    E -->|Fetch status.json| F["💻 Client Browser\n(index.html HUD)"]
```

---

## 🚀 Local Setup & Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/murderszn/stockscan.git
cd stockscan
```

### 2. Set up virtual environment & dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install --with-deps chromium
```

### 3. Run the scraper locally

```bash
python scrape.py
```

This updates `status.json` with live store data:

```json
{
  "product": "Ubiquiti Pro Max 16 PoE",
  "sku": "690207",
  "url": "https://www.microcenter.com/product/690207/ubiquiti-pro-max-16-poe-25g-1g-managed-network-switch-with-etherlighting",
  "store_id": "151",
  "store_label": "Chicago, IL",
  "store_address": "2645 N Elston Ave",
  "price": "$399.99",
  "in_stock": false,
  "message": "OUT OF STOCK",
  "last_checked": "2026-07-18T21:08:43.446977+00:00",
  "checking": false,
  "error": null
}
```

### 4. View the HUD

Open `index.html` directly in any web browser or serve via Python:

```bash
python3 -m http.server 8000
```

Visit `http://localhost:8000` in your browser.

---

## 🛠️ Configuration & Customization

To track a different product or Micro Center location, edit the constants at the top of [`scrape.py`](file:///Users/jahflyx/stockscan/scrape.py):

```python
STORE_ID = "151"          # Micro Center Store ID (e.g. 151 = Chicago, IL)
STORE_LABEL = "Chicago, IL"
STORE_ADDRESS = "2645 N Elston Ave"
PRODUCT_URL = "https://www.microcenter.com/product/690207/..."
PRODUCT_NAME = "Ubiquiti Pro Max 16 PoE"
PRODUCT_SKU = "690207"
```

To adjust the scan frequency, edit the cron schedule in [`.github/workflows/scrape.yml`](file:///Users/jahflyx/stockscan/.github/workflows/scrape.yml):

```yaml
on:
  schedule:
    # Every 15 minutes
    - cron: "*/15 * * * *"
```

---

## 🧑‍💻 Author

Crafted by **murderszn** w/ `<3`
