import yfinance as yf
import json

tickers = ["MXRF11.SA", "PETR4.SA"]
for t_name in tickers:
    print(f"--- {t_name} ---")
    t = yf.Ticker(t_name)
    info = t.info
    # print(json.dumps(info, indent=2)) # Too big
    print(f"Price: {info.get('currentPrice') or info.get('regularMarketPrice')}")
    print(f"Dividend Rate: {info.get('dividendRate')}")
    print(f"Dividend Yield: {info.get('dividendYield')}")
    print(f"Last Dividend Value: {info.get('lastDividendValue')}")
    
    # Check dividends history
    divs = t.dividends
    if not divs.empty:
        print(f"Last Dividends:\n{divs.tail(3)}")
        print(f"Total Dividends (last 12m): {divs.tail(12).sum()}")
    
    # Check calendar (upcoming)
    try:
        cal = t.calendar
        print(f"Calendar:\n{cal}")
    except:
        print("No calendar info")
