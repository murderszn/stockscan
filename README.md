# stockscan

Tony Stark–style Micro Center stock HUD for the **Ubiquiti Pro Max 16 PoE** (SKU `690207`) at **Chicago** (2645 N Elston Ave).

**Live page:** https://murderszn.github.io/stockscan/

made by murderszn w/ &lt;3

## What it does

- Static GitHub Pages HUD (`index.html`) reads `status.json`
- GitHub Action scrapes Micro Center every 30 minutes (and on demand) via Playwright
- Shows stock status, price, SKU, and store location

## Local scrape

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
python scrape.py
```

Open `index.html` in a browser (or any static server).

## Manual refresh on GitHub

Actions → **Scrape stock** → **Run workflow**
