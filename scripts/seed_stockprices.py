#!/usr/bin/env python3
"""Seed the StockPrice table with a curated set of symbols.

This script will:
 - fetch the S&P 500 constituents (tries pandas.read_html, falls back to lightweight parse)
 - add a curated small list for Denmark, Sweden and Norway
 - add top-10 crypto USD tickers
 - call ensure_stock_in_db for each symbol (inserting or updating rows)

Run without args to execute. Use --dry-run to only print actions.
"""
import sys
import time
import argparse
import requests
import re
import os

# Ensure project root is on sys.path so we can import `app` when running as a script
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.database import SessionLocal
from app.services.stocks import ensure_stock_in_db
from pathlib import Path
import json


def fetch_sp500_symbols() -> list:
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    print("Fetching S&P 500 list from Wikipedia...", file=sys.stderr)
    try:
        # Try pandas if available for robust parsing
        try:
            import pandas as pd
            df = pd.read_html(url, header=0)[0]
            syms = df['Symbol'].astype(str).tolist()
            print(f"Found {len(syms)} symbols via pandas", file=sys.stderr)
            return [s.strip() for s in syms if s.strip()]
        except Exception:
            pass

        r = requests.get(url, timeout=15)
        r.raise_for_status()
        html = r.text
        # Find the first wikitable sortable and extract symbols from first td in each row
        m = re.search(r"<table class=\"wikitable sortable\".*?</table>", html, flags=re.S)
        if not m:
            print("Failed to locate the S&P500 table on the page", file=sys.stderr)
            return []
        table = m.group(0)
        rows = re.findall(r"<tr>(.*?)</tr>", table, flags=re.S)
        syms = []
        for row in rows[1:]:
            cols = re.findall(r"<td.*?>(.*?)</td>", row, flags=re.S)
            if not cols:
                continue
            # symbol is typically the first column (may contain anchors)
            raw = cols[0]
            # strip HTML tags
            sym = re.sub(r"<.*?>", "", raw).strip()
            if sym:
                syms.append(sym)
        print(f"Parsed {len(syms)} symbols from Wikipedia table", file=sys.stderr)
        return syms
    except Exception as e:
        print("Error fetching S&P500 list:", e, file=sys.stderr)
        return []


def main(dry_run: bool = False):
    # Prefer static symbols.json in the repo for reliability; fallback to live fetch
    repo_symbols = []
    try:
        data_path = Path(__file__).resolve().parents[1] / 'app' / 'data' / 'symbols.json'
        if data_path.exists():
            repo_symbols = json.loads(data_path.read_text())
            repo_symbols = [s.get('symbol') for s in repo_symbols if isinstance(s, dict) and s.get('symbol')]
    except Exception:
        repo_symbols = []

    sp500 = repo_symbols or fetch_sp500_symbols()

    # Curated Nordic lists (small, safe set)
    denmark = [
    'NOVO-B.CO',     # Novo Nordisk B
    'MAERSK-B.CO',   # A.P. Møller - Mærsk B
    'DANSKE.CO',     # Danske Bank
    'VWS.CO',        # Vestas Wind Systems
    'CARL-B.CO',     # Carlsberg B
    'DSV.CO',        # DSV A/S
    'GN.CO',         # GN Store Nord
    'DEMANT.CO',     # Demant A/S
    'FLS.CO',        # FLSmidth & Co.
    'TRYG.CO',       # Tryg A/S
    'NETC.CO',       # Netcompany Group
    'PNDORA.CO',     # Pandora A/S
    'JYSK.CO',       # Jyske Bank
    'RBREW.CO',      # Royal Unibrew
    'ORSTED.CO',     # Ørsted A/S
    'NSIS-B.CO',     # Novozymes B (nu en del af Novonesis, men bruges stadig)
    'ROCK-B.CO',     # Rockwool International B
    'BAVA.CO',       # Bavarian Nordic
    'COLO-B.CO',     # Coloplast B
    'HLUN-A.CO',     # Lundbeck
    'DEMANT.CO',     # William Demant Holding (nu Demant, men symbolet virker stadig)
    'AMBU-B.CO',     # Ambu B
    ]
    sweden = [
        'VOLV-B.ST',
        'ERIC-B.ST',
        'HM-B.ST',
        'ATCO-A.ST',
    ]
    norway = [
        'EQNR.OL',
        'YAR.OL',
        'DNB.OL',
        'ORK.OL',
    ]

    crypto = [
        'BTC-USD', 'ETH-USD', 'USDT-USD', 'BNB-USD', 'USDC-USD',
        'XRP-USD', 'ADA-USD', 'DOGE-USD', 'DOT-USD', 'TRX-USD'
    ]

    # Compose final list: repo S&P (or fetched list) + cryptos + nordic curated
    symbols = []
    if sp500:
        symbols.extend(sp500)
    else:
        print("Warning: S&P 500 list empty; proceeding with Nordics + crypto only", file=sys.stderr)

    symbols.extend(crypto)
    symbols.extend(denmark)
    symbols.extend(sweden)
    symbols.extend(norway)

    print(f"Total symbols to process: {len(symbols)}", file=sys.stderr)

    added = 0
    updated = 0
    start = time.time()

    db = SessionLocal()
    try:
        for i, sym in enumerate(symbols, 1):
            sym = sym.strip()
            if not sym:
                continue
            print(f"[{i}/{len(symbols)}] Processing {sym}...", file=sys.stderr)
            if dry_run:
                continue
            try:
                sp = ensure_stock_in_db(db, sym)
                # ensure_stock_in_db does commit and refresh; we can't easily know added vs updated without probing
                # We'll treat non-zero price rows as updated/added
                if sp.current_price:
                    updated += 1
                else:
                    added += 1
            except Exception as e:
                print(f"  Failed for {sym}: {e}", file=sys.stderr)
    finally:
        db.close()

    elapsed = time.time() - start
    print("-- Summary --")
    print(f"Symbols processed: {len(symbols)}")
    print(f"Rows with non-zero price (approx): {updated}")
    print(f"Rows with zero price (approx): {added}")
    print(f"Elapsed: {elapsed:.1f}s")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Only print what would be done')
    args = parser.parse_args()
    main(dry_run=args.dry_run)
