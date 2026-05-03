"""
clean_data.py
-------------
Take the raw price + factor CSVs from data/raw/, align them on a common
trading-day index, drop missing rows, compute simple daily returns, and
write tidy outputs to data/processed/.

Outputs:
    data/processed/prices.csv         <- aligned adjusted-close prices
    data/processed/returns.csv        <- daily simple returns per ETF
    data/processed/factors.csv        <- aligned FF factors + RF rate
    data/processed/excess_returns.csv <- ETF returns minus daily RF rate

Run:
    python scripts/clean_data.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import ALL_TICKERS, PROCESSED_DIR, RAW_DIR


def load_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load the two raw CSVs as DataFrames with a parsed Date index."""
    prices = pd.read_csv(RAW_DIR / "prices.csv",
                         parse_dates=["Date"], index_col="Date")
    factors = pd.read_csv(RAW_DIR / "ff_factors.csv",
                          parse_dates=["Date"], index_col="Date")
    return prices, factors


def align_and_clean(prices: pd.DataFrame,
                    factors: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Inner-join prices and factors on the date index, drop NA rows.

    Why inner-join? Yahoo and Kenneth French use slightly different US
    trading-day calendars in edge cases (e.g. half-days), so taking the
    intersection guarantees every row in our processed dataset has a
    complete observation for every ticker AND every factor.
    """
    common_idx = prices.index.intersection(factors.index)
    prices_aligned  = prices.loc[common_idx].dropna(how="any")
    factors_aligned = factors.loc[prices_aligned.index]
    return prices_aligned, factors_aligned


def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Daily simple returns: r_t = P_t / P_{t-1} - 1.

    The first row is NaN by construction; we drop it.
    """
    returns = prices.pct_change().dropna(how="any")
    return returns


def compute_excess_returns(returns: pd.DataFrame,
                           factors: pd.DataFrame) -> pd.DataFrame:
    """Return r_i - r_f for every ticker, indexed by date.

    The Fama-French RF rate is already a daily decimal at this point.
    """
    rf = factors["RF"].reindex(returns.index)
    excess = returns.sub(rf, axis=0)
    return excess


def summarise_coverage(prices: pd.DataFrame, returns: pd.DataFrame) -> str:
    """Human-readable diagnostic string written next to the processed data."""
    lines = [
        "Cleaned dataset summary",
        "-----------------------",
        f"Date range : {returns.index.min().date()} -> {returns.index.max().date()}",
        f"Trading days: {len(returns):,}",
        f"Tickers     : {list(returns.columns)}",
        "",
        "Per-ticker first valid observation:",
    ]
    for col in prices.columns:
        first_valid = prices[col].first_valid_index()
        lines.append(f"  {col:6s} -> {first_valid.date() if first_valid else 'n/a'}")
    return "\n".join(lines)


def main() -> None:
    print("=== clean_data.py ===")

    prices, factors = load_raw()
    print(f"  raw prices : {prices.shape}")
    print(f"  raw factors: {factors.shape}")

    prices, factors = align_and_clean(prices, factors)
    print(f"  aligned    : {prices.shape}")

    # Sanity check: every expected ticker should be present.
    missing = set(ALL_TICKERS) - set(prices.columns)
    if missing:
        raise RuntimeError(f"Missing tickers in price data: {missing}")

    returns = compute_returns(prices)
    excess  = compute_excess_returns(returns, factors)

    # Persist
    prices.to_csv(PROCESSED_DIR  / "prices.csv")
    returns.to_csv(PROCESSED_DIR / "returns.csv")
    factors.to_csv(PROCESSED_DIR / "factors.csv")
    excess.to_csv(PROCESSED_DIR  / "excess_returns.csv")

    summary = summarise_coverage(prices, returns)
    (PROCESSED_DIR / "summary.txt").write_text(summary + "\n")
    print("\n" + summary)
    print("\nDone.")


if __name__ == "__main__":
    main()
