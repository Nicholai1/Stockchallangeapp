import yfinance as yf


def get_stock_info(symbol: str):
    try:
        ticker = yf.Ticker(symbol)
        # Prøv fast_info først
        try:
            fast = ticker.fast_info
            price = fast.get("last_price")
        except Exception:
            price = None

        # Fallback til sidste lukkekurs
        if not price:
            hist = ticker.history(period="1d")
            if not hist.empty:
                price = hist["Close"].iloc[-1]

        price = round(price, 2) if price else 0

        return {
            "symbol": symbol,
            "name": ticker.info.get("shortName", symbol),
            "price": price,
            "currency": ticker.info.get("currency", "N/A")
        }

    except Exception as e:
        print(f"Fejl ved hentning af {symbol}: {e}")
        return {"symbol": symbol, "name": symbol, "price": 0, "currency": "N/A"}
