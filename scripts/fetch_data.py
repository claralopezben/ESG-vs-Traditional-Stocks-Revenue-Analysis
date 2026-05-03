"""
fetch_data.py
-------------
Download (i) daily adjusted close prices for the six study ETFs from
Yahoo Finance, and (ii) the Fama-French 3-factor daily series + risk-free
rate from Kenneth French's Data Library, and write them as CSVs to
data/raw/.

Run:
    python scripts/fetch_data.py
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Allow `python scripts/fetch_data.py` from project root
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (ALL_TICKERS, END_DATE, RAW_DIR, START_DATE)


def fetch_prices(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    """Download adjusted close prices for `tickers` between `start` and `end`.

    Yahoo's API can flake; we download all tickers in one batch and let
    yfinance handle threading. The function returns a wide DataFrame with
    one column per ticker and a DatetimeIndex.
    """
    import yfinance as yf

    print(f"  Downloading {len(tickers)} tickers from Yahoo Finance...")
    df = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        auto_adjust=True,        # use adjusted close as Close
        progress=False,
        group_by="ticker",
    )

    # yfinance returns a MultiIndex (ticker, field) when more than one ticker
    # is requested. We flatten to just the Close column per ticker.
    if isinstance(df.columns, pd.MultiIndex):
        prices = pd.DataFrame({t: df[t]["Close"] for t in tickers})
    else:
        prices = df[["Close"]].rename(columns={"Close": tickers[0]})

    prices.index.name = "Date"
    return prices


def fetch_fama_french(start: str, end: str) -> pd.DataFrame:
    """Download the daily Fama-French 3 factors + risk-free rate (US).

    Kenneth French publishes the factors as percentage points; we convert
    to decimals. Columns returned: Mkt-RF, SMB, HML, RF.
    """
    from pandas_datareader import data as pdr

    print("  Downloading Fama-French 3 factors...")
    ff = pdr.DataReader(
        "F-F_Research_Data_Factors_daily",
        "famafrench",
        start=start,
        end=end,
    )[0]

    ff = ff / 100.0                          # percent -> decimals
    ff.index = pd.to_datetime(ff.index)
    ff.index.name = "Date"
    return ff


def main() -> None:
    print("=== fetch_data.py ===")
    print(f"Window: {START_DATE} to {END_DATE}\n")

    # --- ETF prices -------------------------------------------------------
    prices = fetch_prices(list(ALL_TICKERS.keys()), START_DATE, END_DATE)
    out_path = RAW_DIR / "prices.csv"
    prices.to_csv(out_path)
    print(f"  -> wrote {out_path} ({prices.shape[0]} rows, "
          f"{prices.shape[1]} cols)")

    # --- Fama-French factors ---------------------------------------------
    ff = fetch_fama_french(START_DATE, END_DATE)
    ff_path = RAW_DIR / "ff_factors.csv"
    ff.to_csv(ff_path)
    print(f"  -> wrote {ff_path} ({ff.shape[0]} rows)")

    # Provenance footnote
    meta_path = RAW_DIR / "ff_factors_meta.txt"
    meta_path.write_text(
        f"Fama-French 3 factors daily, downloaded {datetime.utcnow():%Y-%m-%d %H:%M UTC}\n"
        f"Source: Kenneth R. French Data Library via pandas_datareader\n"
        f"Range: {ff.index.min().date()} to {ff.index.max().date()}\n"
    )

    print("\nDone.")


if __name__ == "__main__":
    main()
